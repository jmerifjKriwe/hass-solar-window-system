"""Config flow for Solar Window System integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN
from .options_flow import SolarWindowSystemOptionsFlow

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.data_entry_flow import FlowResult

_LOGGER = logging.getLogger(__name__)

# Constants for entry types
ENTRY_TYPE_GLOBAL = "global_config"
ENTRY_TYPE_GROUPS = "group_configs"
ENTRY_TYPE_WINDOWS = "window_configs"


class GroupSubentryFlowHandler(config_entries.ConfigSubentryFlow):
    """Handle subentry flow for adding and modifying a group."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """User flow to add a new group."""
        _LOGGER.warning("🔧 GroupSubentryFlowHandler.async_step_user called")
        _LOGGER.warning("🔧 User input: %s", user_input)

        if user_input is not None:
            _LOGGER.warning("🔧 Creating subentry for group: %s", user_input["name"])
            result = self.async_create_entry(
                title=user_input["name"],
                data={"entry_type": "group", "name": user_input["name"]},
            )
            _LOGGER.warning("🔧 Subentry created: %s", result)
            return result

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required("name"): str})
        )


class WindowSubentryFlowHandler(config_entries.ConfigSubentryFlow):
    """Handle subentry flow for adding and modifying a window."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """User flow to add a new window."""
        _LOGGER.warning("🔧 WindowSubentryFlowHandler.async_step_user called")
        _LOGGER.warning("🔧 User input: %s", user_input)

        if user_input is not None:
            _LOGGER.warning("🔧 Creating subentry for window: %s", user_input["name"])
            result = self.async_create_entry(
                title=user_input["name"],
                data={"entry_type": "window", "name": user_input["name"]},
            )
            _LOGGER.warning("🔧 Subentry created: %s", result)
            return result

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required("name"): str})
        )


class SolarWindowSystemConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solar Window System."""

    VERSION = 1
    _created = False

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[config_entries.ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        # Return only the subentry type relevant for this specific config entry
        if config_entry.data.get("entry_type") == ENTRY_TYPE_GROUPS:
            return {"group": GroupSubentryFlowHandler}
        if config_entry.data.get("entry_type") == ENTRY_TYPE_WINDOWS:
            return {"window": WindowSubentryFlowHandler}
        # Fallback: return all types if entry type is unclear
        return {"group": GroupSubentryFlowHandler, "window": WindowSubentryFlowHandler}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._created or self._already_configured():
            return self.async_abort(reason="no_more_entries")

        if user_input is not None:
            # Create three entries
            await self._create_entries()
            self._created = True
            return self.async_create_entry(title="Solar Window System", data={})

        return self.async_show_form(step_id="user", description_placeholders={})

    async def async_step_internal(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle internal flow for creating sub-entries."""
        if user_input is None:
            return self.async_abort(reason="missing_data")

        entry_type = user_input.get("entry_type")
        if entry_type == ENTRY_TYPE_GROUPS:
            # Mark this entry as a subentry parent in the data
            return self.async_create_entry(
                title="Group configurations",
                data={"entry_type": ENTRY_TYPE_GROUPS, "is_subentry_parent": True},
            )
        if entry_type == ENTRY_TYPE_WINDOWS:
            # Mark this entry as a subentry parent in the data
            return self.async_create_entry(
                title="Window configurations",
                data={"entry_type": ENTRY_TYPE_WINDOWS, "is_subentry_parent": True},
            )

        return self.async_abort(reason="unknown_entry_type")

    def _already_configured(self) -> bool:
        """Check if the integration is already configured."""
        return any(entry.domain == DOMAIN for entry in self._async_current_entries())

    async def _create_entries(self) -> None:
        """Create the three required entries."""
        # Create Group configurations entry
        await self.hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "internal"},
            data={"entry_type": ENTRY_TYPE_GROUPS},
        )

        # Create Window configurations entry
        await self.hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "internal"},
            data={"entry_type": ENTRY_TYPE_WINDOWS},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> SolarWindowSystemOptionsFlow:
        """Return the options flow handler."""
        return SolarWindowSystemOptionsFlow(config_entry)
