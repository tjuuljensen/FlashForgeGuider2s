import logging
from datetime import timedelta
from typing import Any, Callable, Dict, Optional, TypedDict

import async_timeout
from homeassistant import config_entries, core
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
import voluptuous as vol

from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .protocol import get_print_job_status

LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required('ip'): cv.string,
        vol.Required('port'): cv.string,
    }
)

class PrinterDefinition(TypedDict):
    ip: str
    port: int


async def get_coordinator(hass, config_entry, config):
    """Reuse a single coordinator per config entry."""
    if config_entry.options:
        config.update(config_entry.options)
    coordinator = hass.data[DOMAIN][config_entry.entry_id].get("coordinator")
    if coordinator is None:
        coordinator = FlashforgeGuider2sCoordinator(
            hass,
            config,
            scan_interval=config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = coordinator
    return coordinator


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: Callable,
) -> bool:
    config = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = await get_coordinator(hass, config_entry, config)
    sensors = [
        FlashforgeGuider2sStateSensor(coordinator, config),
        FlashforgeGuider2sProgressSensor(coordinator, config),
    ]
    async_add_entities(sensors, update_before_add=True)


class FlashforgeGuider2sCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, printer_definition: PrinterDefinition, scan_interval: int):
        super().__init__(
            hass,
            LOGGER,
            name='FlashForge Guider 2s',
            update_interval=timedelta(seconds=scan_interval),
        )
        self.ip = printer_definition['ip_address']
        self.port = printer_definition['port']

    async def _async_update_data(self):
        async with async_timeout.timeout(5):
            try:
                return await get_print_job_status(self.ip, self.port)
            except Exception:  # noqa: BLE001 - surface connection issues as offline
                return {'online': False}


class FlashforgeGuider2sCommonPropertiesMixin:
    @property
    def name(self) -> str:
        return f'FlashForge Guider 2s'

    @property
    def unique_id(self) -> str:
        return f'flashforge_guider2s_{self.ip}'

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.ip)},
            "name": "FlashForge Guider 2s",
            "manufacturer": "FlashForge",
            "model": "Guider 2s",
        }


class BaseFlashforgeGuider2sSensor(FlashforgeGuider2sCommonPropertiesMixin, CoordinatorEntity, Entity):
    def __init__(self, coordinator: DataUpdateCoordinator, printer_definition: PrinterDefinition) -> None:
        super().__init__(coordinator)
        self.ip = printer_definition['ip_address']
        self.port = printer_definition['port']
        self._available = False
        self.attrs = {}

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        return self.attrs

    @callback
    def _handle_coordinator_update(self) -> None:
        self.attrs = self.coordinator.data
        self.async_write_ha_state()


class FlashforgeGuider2sStateSensor(BaseFlashforgeGuider2sSensor):
    @property
    def name(self) -> str:
        return f'{super().name} state'

    @property
    def unique_id(self) -> str:
        return f'{super().unique_id}_state'

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self) -> Optional[str]:
        if self.attrs.get('online'):
            if self.attrs.get('printing'):
                return 'printing'
            else:
                return 'online'
        else:
            return 'offline'

    @property
    def icon(self) -> str:
        return 'mdi:printer-3d'


class FlashforgeGuider2sProgressSensor(BaseFlashforgeGuider2sSensor):
    @property
    def name(self) -> str:
        return f'{super().name} progress'

    @property
    def unique_id(self) -> str:
        return f'{super().unique_id}_progress'

    @property
    def available(self) -> bool:
        return bool(self.attrs.get('online'))

    @property
    def state(self) -> Optional[str]:
        return self.attrs.get('progress', 0)

    @property
    def icon(self) -> str:
        return 'mdi:percent-circle'

    @property
    def unit_of_measurement(self) -> str:
        return '%'
