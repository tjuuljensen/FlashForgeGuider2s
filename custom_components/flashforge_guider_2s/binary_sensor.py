from __future__ import annotations

import logging
from typing import Callable

from homeassistant import config_entries, core
from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import DOMAIN
from .sensor import FlashforgeGuider2sCommonPropertiesMixin, get_coordinator

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities: Callable,
) -> bool:
    config = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = await get_coordinator(hass, config_entry, config)
    async_add_entities(
        [
            FlashforgeGuider2sOnlineBinarySensor(coordinator, config),
        ],
        update_before_add=True,
    )


class FlashforgeGuider2sOnlineBinarySensor(
    FlashforgeGuider2sCommonPropertiesMixin, BinarySensorEntity
):
    """Indicates if the printer is online."""

    def __init__(self, coordinator, printer_definition) -> None:
        self.coordinator = coordinator
        self.ip = printer_definition['ip_address']
        self.port = printer_definition['port']
        self._available = False
        self.attrs = {}

    @property
    def name(self) -> str:
        return f'{super().name} online'

    @property
    def unique_id(self) -> str:
        return f'{super().unique_id}_online'

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.get('online'))

    @property
    def extra_state_attributes(self):
        return self.coordinator.data

    async def async_update(self):
        await self.coordinator.async_request_refresh()
