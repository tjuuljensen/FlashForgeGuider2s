from __future__ import annotations

from typing import Any, Dict, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_PRINTERS,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .protocol import get_print_job_status


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.positive_int,
    }
)


class FlashforgeGuider2sConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for FlashForge Guider 2s."""

    VERSION = 1
    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            try:
                status = await get_print_job_status(
                    user_input[CONF_IP_ADDRESS],
                    user_input[CONF_PORT],
                )
                if not status.get("online"):
                    errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - surface connection issues as cannot_connect
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(user_input[CONF_IP_ADDRESS])
                self._abort_if_unique_id_configured()

                self.data = user_input
                self.data.setdefault(CONF_PRINTERS, [])
                self.data.setdefault(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

                return self.async_create_entry(
                    title="FlashForge Guider 2s",
                    data=self.data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors,
        )

    async def async_step_import(self, user_input: Dict[str, Any]) -> FlowResult:
        """Handle YAML import for backward compatibility."""
        return await self.async_step_user(user_input)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return FlashforgeGuider2sOptionsFlow(config_entry)


class FlashforgeGuider2sOptionsFlow(config_entries.OptionsFlow):
    """Handle options for the integration."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=OPTIONS_SCHEMA,
        )
