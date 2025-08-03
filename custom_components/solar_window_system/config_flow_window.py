"""
Window-specific config flow steps for the solar_window_system integration.
"""

from homeassistant.helpers import selector
import voluptuous as vol


class SolarWindowConfigFlowWindow:
    """Window-specific config flow steps (extracted from main config_flow)."""

    def __init__(self, parent):
        """Initialize with reference to parent config flow."""
        self.parent = parent

    async def async_step_window_init(self, user_input=None):
        """Handle the window init step. Only cross-field validation, rely on schema for type/range. Fügt Group-Auswahl hinzu."""
        CONF_ENTRY_TYPE = "entry_type"
        CONF_WINDOW_NAME = "name"
        # Alle vorhandenen Groups sammeln
        group_entries = [
            entry
            for entry in self.parent._async_current_entries()
            if entry.data.get(CONF_ENTRY_TYPE) == "group"
        ]
        group_names = [
            entry.data.get("name") for entry in group_entries if entry.data.get("name")
        ]
        group_choices = {name: name for name in group_names}

        global_entry = next(
            (
                entry
                for entry in self.parent._async_current_entries()
                if entry.data.get(CONF_ENTRY_TYPE) == "global"
            ),
            None,
        )
        defaults = global_entry.options if global_entry else {}
        errors = {}
        if user_input is not None:
            # Check required entity fields
            if user_input.get("room_temp_entity") in (None, ""):
                errors["room_temp_entity"] = "required_entity"
            # Only cross-field validation
            elevation_min = user_input.get("elevation_min")
            elevation_max = user_input.get("elevation_max")
            if (
                elevation_min is not None
                and elevation_max is not None
                and elevation_min > elevation_max
            ):
                errors["elevation_min"] = "min_greater_than_max"
                errors["elevation_max"] = "max_less_than_min"
            if not errors:
                self.parent._user_input = user_input.copy()
                self.parent._user_input[CONF_ENTRY_TYPE] = "window"
                for key in ["tilt", "g_value", "frame_width"]:
                    if key in self.parent._user_input and self.parent._user_input[
                        key
                    ] == defaults.get(key):
                        self.parent._user_input.pop(key)
                return await self.parent.async_step_window_overrides()
        window_name = (user_input or {}).get(CONF_WINDOW_NAME) or defaults.get(
            CONF_WINDOW_NAME, ""
        )
        schema_dict = {
            vol.Required(
                CONF_WINDOW_NAME, default=defaults.get(CONF_WINDOW_NAME, "")
            ): str,
            vol.Required("azimuth", default=defaults.get("azimuth", 180)): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=360)
            ),
            vol.Required(
                "azimuth_min", default=defaults.get("azimuth_min", 0)
            ): vol.All(vol.Coerce(float), vol.Range(min=-90, max=0)),
            vol.Required(
                "azimuth_max", default=defaults.get("azimuth_max", 0)
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Required(
                "elevation_min", default=defaults.get("elevation_min", 0)
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Required(
                "elevation_max", default=defaults.get("elevation_max", 0)
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
            vol.Required("width", default=defaults.get("width", 1.0)): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=10)
            ),
            vol.Required("height", default=defaults.get("height", 1.0)): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=10)
            ),
            vol.Required(
                "shadow_depth", default=defaults.get("shadow_depth", 0)
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=5)),
            vol.Required(
                "shadow_offset", default=defaults.get("shadow_offset", 0)
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=5)),
            vol.Required(
                "room_temp_entity", default=defaults.get("room_temp_entity")
            ): selector.EntitySelector(
                {"domain": "sensor", "device_class": "temperature"}
            ),
            vol.Optional("tilt", default=defaults.get("tilt")): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=90)
            ),
            vol.Optional("g_value", default=defaults.get("g_value")): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=0.9)
            ),
            vol.Optional("frame_width", default=defaults.get("frame_width")): vol.All(
                vol.Coerce(float), vol.Range(min=0.05, max=0.3)
            ),
        }
        # Group-Auswahl ergänzen, falls Groups existieren
        if group_names:
            schema_dict[vol.Optional("group")] = vol.In(group_choices)

        return self.parent.async_show_form(
            step_id="window_init",
            data_schema=vol.Schema(schema_dict),
            description_placeholders={
                "tilt": str(defaults.get("tilt", 90)),
                "g_value": str(defaults.get("g_value", 0.5)),
                "frame_width": str(defaults.get("frame_width", 0.125)),
                "name": window_name,
            },
            errors=errors,
        )

    async def async_step_window_overrides(self, user_input=None):
        """Handle window override step."""
        CONF_ENTRY_TYPE = "entry_type"
        global_entry = next(
            (
                entry
                for entry in self.parent._async_current_entries()
                if entry.data.get(CONF_ENTRY_TYPE) == "global"
            ),
            None,
        )
        defaults = global_entry.options if global_entry else {}

        if user_input is not None:
            self.parent._user_input.update(user_input)
            # Remove defaults
            for key in list(self.parent._user_input.keys()):
                if (
                    self.parent._user_input[key] == defaults.get(key)
                    or self.parent._user_input[key] is None
                ):
                    self.parent._user_input.pop(key)

            return self.parent.async_create_entry(
                title=self.parent._user_input["name"],
                data=self.parent._user_input,
                options={},
            )

        return self.parent.async_show_form(
            step_id="window_overrides",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "diffuse_factor", default=defaults.get("diffuse_factor")
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.5)),
                    vol.Optional(
                        "threshold_direct", default=defaults.get("threshold_direct")
                    ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                    vol.Optional(
                        "threshold_diffuse", default=defaults.get("threshold_diffuse")
                    ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                    vol.Optional(
                        "indoor_base", default=defaults.get("indoor_base")
                    ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                    vol.Optional(
                        "outdoor_base", default=defaults.get("outdoor_base")
                    ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                    vol.Optional(
                        "scenario_b_temp_indoor_threshold",
                        default=defaults.get("scenario_b_temp_indoor_threshold"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_b_temp_outdoor_threshold",
                        default=defaults.get("scenario_b_temp_outdoor_threshold"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_c_temp_forecast_threshold",
                        default=defaults.get("scenario_c_temp_forecast_threshold"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_c_temp_indoor_threshold",
                        default=defaults.get("scenario_c_temp_indoor_threshold"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_c_temp_outdoor_threshold",
                        default=defaults.get("scenario_c_temp_outdoor_threshold"),
                    ): vol.Coerce(float),
                    vol.Optional(
                        "scenario_c_start_hour",
                        default=defaults.get("scenario_c_start_hour"),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                }
            ),
            last_step=True,
            description_placeholders={"name": self.parent._user_input.get("name", "")},
        )
