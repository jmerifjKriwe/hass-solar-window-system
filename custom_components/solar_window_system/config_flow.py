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

_LOGGER = logging.getLogger(__name__)

# Constants for entry types
ENTRY_TYPE_GLOBAL = "global_config"
ENTRY_TYPE_GROUPS = "group_configs"
ENTRY_TYPE_WINDOWS = "window_configs"


class GroupSubentryFlowHandler(config_entries.ConfigSubentryFlow):
    """
    Handle subentry flow for adding and modifying a group.

    Two-step wizard:
    - user (basic): name + core thresholds
    - enhanced: scenario enable + scenario thresholds
    """

    def __init__(self) -> None:
        """Initialize the group subentry flow handler."""
        self._basic: dict[str, Any] = {}
        self._reconfigure_mode: bool = False

    # ----- Creation flow (step 1: basic) -----
    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
        """Render basic group configuration (page 1)."""
        _LOGGER.debug("GroupSubentryFlowHandler.user: input=%s", user_input)

        # Defaults for basic page
        defaults: dict[str, Any] = {
            "name": getattr(getattr(self, "subentry", None), "title", ""),
            "diffuse_factor": 0.15,
            "threshold_direct": 200,
            "threshold_diffuse": 150,
            "temperature_indoor_base": 23.0,
            "temperature_outdoor_base": 19.5,
        }

        # If reconfiguring, prefill from current subentry title and data
        if self.source == config_entries.SOURCE_RECONFIGURE:
            sub = self._get_reconfigure_subentry()
            if getattr(sub, "title", None):
                defaults["name"] = sub.title
            for key in list(defaults.keys()):
                if key == "name":
                    continue
                if key in sub.data:
                    defaults[key] = sub.data[key]

        schema = vol.Schema(
            {
                vol.Required("name", default=defaults["name"]): str,
                vol.Required(
                    "diffuse_factor", default=defaults["diffuse_factor"]
                ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.5)),
                vol.Required(
                    "threshold_direct", default=defaults["threshold_direct"]
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=1000)),
                vol.Required(
                    "threshold_diffuse", default=defaults["threshold_diffuse"]
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=1000)),
                vol.Required(
                    "temperature_indoor_base",
                    default=defaults["temperature_indoor_base"],
                ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Required(
                    "temperature_outdoor_base",
                    default=defaults["temperature_outdoor_base"],
                ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
            }
        )

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=schema)

        # Store and continue to enhanced page
        self._basic = user_input
        return await self.async_step_enhanced()

    # ----- Creation flow (step 2: enhanced) -----
    async def async_step_enhanced(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Render enhanced group configuration (page 2)."""
        _LOGGER.debug("GroupSubentryFlowHandler.enhanced: input=%s", user_input)

        enhanced_defaults: dict[str, Any] = {
            "scenario_b_enable": "inherit",
            "scenario_b_temp_indoor": 23.5,
            "scenario_b_temp_outdoor": 25.5,
            "scenario_c_enable": "inherit",
            "scenario_c_temp_indoor": 21.5,
            "scenario_c_temp_outdoor": 24.0,
            "scenario_c_temp_forecast": 28.5,
            "scenario_c_start_hour": 9,
        }

        # On reconfigure, prefill from existing subentry data
        if self.source == config_entries.SOURCE_RECONFIGURE:
            sub = self._get_reconfigure_subentry()
            for key in list(enhanced_defaults.keys()):
                if key in sub.data:
                    enhanced_defaults[key] = sub.data[key]

        enable_options = ["disable", "enable", "inherit"]

        schema = vol.Schema(
            {
                vol.Required(
                    "scenario_b_enable", default=enhanced_defaults["scenario_b_enable"]
                ): vol.In(enable_options),
                vol.Required(
                    "scenario_b_temp_indoor",
                    default=enhanced_defaults["scenario_b_temp_indoor"],
                ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Required(
                    "scenario_b_temp_outdoor",
                    default=enhanced_defaults["scenario_b_temp_outdoor"],
                ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Required(
                    "scenario_c_enable", default=enhanced_defaults["scenario_c_enable"]
                ): vol.In(enable_options),
                vol.Required(
                    "scenario_c_temp_indoor",
                    default=enhanced_defaults["scenario_c_temp_indoor"],
                ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Required(
                    "scenario_c_temp_outdoor",
                    default=enhanced_defaults["scenario_c_temp_outdoor"],
                ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Required(
                    "scenario_c_temp_forecast",
                    default=enhanced_defaults["scenario_c_temp_forecast"],
                ): vol.All(vol.Coerce(float), vol.Range(min=15, max=40)),
                vol.Required(
                    "scenario_c_start_hour",
                    default=enhanced_defaults["scenario_c_start_hour"],
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            }
        )

        if user_input is None:
            return self.async_show_form(step_id="enhanced", data_schema=schema)

        # Merge pages and create/update entry (keep name in data to preserve behavior)
        data = {**self._basic, **user_input, "entry_type": "group"}
        name = data["name"]

        # Creation and reconfigure both end with creating/updating subentry data
        if self.source == config_entries.SOURCE_RECONFIGURE:
            entry = self._get_entry()
            subentry = self._get_reconfigure_subentry()
            return self.async_update_and_abort(
                entry,
                subentry,
                title=name,
                data=data,
            )
        return self.async_create_entry(title=name, data=data)

    # ----- Reconfigure entry point (delegates to the same 2-step flow) -----
    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Start reconfigure and reuse user/enhanced steps with defaults."""
        self._reconfigure_mode = True
        return await self.async_step_user(user_input)


class WindowSubentryFlowHandler(config_entries.ConfigSubentryFlow):
    """Handle subentry flow for adding and modifying a window."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
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

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> Any:
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
    ) -> Any:
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
