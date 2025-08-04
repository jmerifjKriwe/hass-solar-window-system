"""Config flow for Solar Window System integration."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigSubentryFlow, OptionsFlow
from homeassistant.core import callback

from .const import (
    CONF_WINDOW,
    CONF_WINDOW_NAME,
    DOMAIN,
    ENTRY_TYPE_MAIN,
    ENTRY_TYPE_WINDOW,
)

_LOGGER = logging.getLogger(__name__)


class SolarWindowSystemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solar Window System."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            # Create the main Solar Window System entry
            return self.async_create_entry(
                title="Solar Window System", data={"entry_type": ENTRY_TYPE_MAIN}
            )

        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))

    async def async_step_auto_create_window_config(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle automatic creation of Window Configuration entry."""
        # Create Window Configuration entry automatically
        return self.async_create_entry(
            title="Window Configuration",
            data={
                "entry_type": "window_configuration",
                "auto_created": True,
            },
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        # Only Window Configuration supports window sub-entries
        # Solar Window System has no sub-entries
        if config_entry.data.get("entry_type") == "window_configuration":
            return {
                "window": WindowSubentryFlowHandler,
            }
        # Solar Window System and other entries return empty dict (no sub-entries)
        return {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return SolarWindowSystemOptionsFlowHandler(config_entry)


class WindowSubentryFlowHandler(ConfigSubentryFlow):
    """Handle a window configuration subentry flow."""

    @property
    def _is_new(self) -> bool:
        """Return if this is a new subentry."""
        return self.source == "user"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.SubentryFlowResult:
        """Handle the user step."""
        errors = {}

        if user_input is not None:
            # Generate unique ID for this window
            unique_id = str(uuid.uuid4())
            window_name = user_input.get(CONF_WINDOW_NAME, "Window")

            if self._is_new:
                return self.async_create_entry(
                    title=f"Window: {window_name}",  # Make the title more descriptive
                    data={
                        CONF_WINDOW_NAME: window_name,
                        CONF_WINDOW: unique_id,
                        "entry_type": ENTRY_TYPE_WINDOW,  # Mark as window entry
                    },
                )

            return self.async_update_and_abort(
                self._get_entry(),
                self._get_reconfigure_subentry(),
                data={
                    CONF_WINDOW_NAME: window_name,
                    CONF_WINDOW: unique_id,
                    "entry_type": ENTRY_TYPE_WINDOW,  # Mark as window entry
                },
                title=window_name,
            )

        # Show configuration form for a window
        data_schema = vol.Schema(
            {
                vol.Required(CONF_WINDOW_NAME): str,
            }
        )

        if not self._is_new:
            # For reconfiguration, add current values
            subentry = self._get_reconfigure_subentry()
            data_schema = self.add_suggested_values_to_schema(
                data_schema, subentry.data
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.SubentryFlowResult:
        """Handle reconfiguration."""
        return await self.async_step_user(user_input)


class SolarWindowSystemOptionsFlowHandler(OptionsFlow):
    """Handle options flow for Solar Window System."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema({})

        return self.async_show_form(step_id="init", data_schema=options_schema)
