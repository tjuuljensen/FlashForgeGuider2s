import asyncio
from typing import Any, Dict

from homeassistant import config_entries, core
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_REFRESH,
)
from .sensor import FlashforgeGuider2sCoordinator


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})
    merged_config: Dict[str, Any] = {**entry.data, **entry.options}
    coordinator = FlashforgeGuider2sCoordinator(
        hass,
        merged_config,
        scan_interval=merged_config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:  # noqa: BLE001 - ensure ConfigEntryNotReady bubbles before platform setup
        raise ConfigEntryNotReady from err

    hass_data: Dict[str, Any] = dict(merged_config)
    hass_data["coordinator"] = coordinator
    # Registers update listener to update config entry when options are updated.
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    hass_data['unsub_options_update_listener'] = unsub_options_update_listener
    hass.data[DOMAIN][entry.entry_id] = hass_data

    async def handle_refresh_service(call) -> None:
        """Force immediate refresh for all configured printers."""
        for entry_data in hass.data.get(DOMAIN, {}).values():
            coordinator = entry_data.get("coordinator")
            if coordinator:
                await coordinator.async_request_refresh()

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_register(DOMAIN, SERVICE_REFRESH, handle_refresh_service)

    # Forward the setup to the sensor and camera platforms.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ['sensor', 'camera', 'binary_sensor'])
    )
    # hass.async_create_task(
    #     hass.config_entries.async_forward_entry_setups(entry, 'camera')
    # )
    return True


async def options_update_listener(
    hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry
):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, 'sensor')],
            *[hass.config_entries.async_forward_entry_unload(entry, 'camera')],
        )
    )
    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]['unsub_options_update_listener']()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the GitHub Custom component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True
