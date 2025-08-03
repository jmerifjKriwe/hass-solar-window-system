import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers import device_registry as dr

from .const import CONF_ENTRY_TYPE, CONF_WINDOW_NAME, DOMAIN


def _get_schema(options: dict | None = None) -> vol.Schema:
    if options is None:
        options = {}

    fields = {
        vol.Required(
            "solar_radiation_sensor",
            default=options.get("solar_radiation_sensor"),
        ): selector.EntitySelector({"domain": "sensor"}),
        vol.Required(
            "outdoor_temperature_sensor",
            default=options.get("outdoor_temperature_sensor"),
        ): selector.EntitySelector({"domain": "sensor", "device_class": "temperature"}),
        vol.Required(
            "update_interval", default=options.get("update_interval", 5)
        ): selector.NumberSelector({"min": 1, "mode": "box"}),
        vol.Required(
            "min_solar_radiation", default=options.get("min_solar_radiation", 50)
        ): selector.NumberSelector({"min": 0, "mode": "box"}),
        vol.Required(
            "min_sun_elevation", default=options.get("min_sun_elevation", 10)
        ): selector.NumberSelector({"min": 0, "max": 90, "mode": "box"}),
    }

    weather_sensor = options.get("weather_warning_sensor")
    fields[
        vol.Optional(
            "weather_warning_sensor",
            default=weather_sensor if weather_sensor else vol.UNDEFINED,
        )
    ] = selector.EntitySelector({"domain": "binary_sensor"})
    if weather_sensor:
        fields[vol.Optional("delete_weather_warning_sensor", default=False)] = (
            selector.BooleanSelector()
        )

    forecast_sensor = options.get("forecast_temperature_sensor")
    fields[
        vol.Optional(
            "forecast_temperature_sensor",
            default=forecast_sensor if forecast_sensor else vol.UNDEFINED,
        )
    ] = selector.EntitySelector({"domain": "sensor", "device_class": "temperature"})
    if forecast_sensor:
        fields[vol.Optional("delete_forecast_temperature_sensor", default=False)] = (
            selector.BooleanSelector()
        )

    return vol.Schema(fields)


class SolarWindowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    _user_input = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import hier, um Zirkularität zu vermeiden
        from . import config_flow_window

        self.window_flow = config_flow_window.SolarWindowConfigFlowWindow(self)

    async def async_step_user(self, user_input=None):
        # Check if a global entry already exists
        global_entry = next(
            (
                entry
                for entry in self.hass.config_entries.async_entries(DOMAIN)
                if entry.data.get(CONF_ENTRY_TYPE) == "global"
            ),
            None,
        )

        if not global_entry:
            # If no global entry, only allow creating a global entry
            return await self.async_step_global_init()

        # If a global entry exists, allow creating a window or a group
        if user_input is not None:
            entry_type = user_input.get(CONF_ENTRY_TYPE)
            if entry_type == "window":
                return await self.async_step_window_init()
            elif entry_type == "group":
                return await self.async_step_group_init()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ENTRY_TYPE): vol.In(["window", "group"]),
                }
            ),
            errors={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        if config_entry.data.get(CONF_ENTRY_TYPE) == "window":
            return SolarWindowOptionsFlowWindow(config_entry)
        if config_entry.data.get(CONF_ENTRY_TYPE) == "group":
            return SolarWindowOptionsFlowGroup(config_entry)
        return SolarWindowOptionsFlowHandler(config_entry)

    async def async_step_global_init(self, user_input=None):
        """Handle the global init step. Only check for required fields, rely on schema for validation."""
        errors = {}
        if user_input is not None:
            # Check required fields
            for field in [
                "solar_radiation_sensor",
                "outdoor_temperature_sensor",
                "update_interval",
                "min_solar_radiation",
                "min_sun_elevation",
            ]:
                if user_input.get(field) in (None, ""):
                    errors[field] = "required"
            if not errors:
                self._user_input.update(user_input)
                return await self.async_step_global_thresholds()
        return self.async_show_form(
            step_id="global_init",
            data_schema=_get_schema(self._user_input),
            errors=errors,
        )

    async def async_step_global_thresholds(self, user_input=None):
        """Handle the global thresholds step. Rely on schema for validation."""
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_global_scenarios()
        schema = vol.Schema(
            {
                vol.Required("g_value", default=0.5): selector.NumberSelector(
                    {"min": 0.1, "max": 0.9, "mode": "box", "step": 0.01}
                ),
                vol.Required("frame_width", default=0.125): selector.NumberSelector(
                    {"min": 0.05, "max": 0.3, "mode": "box", "step": 0.01}
                ),
                vol.Required("tilt", default=90): selector.NumberSelector(
                    {"min": 0, "max": 90, "mode": "box"}
                ),
                vol.Required("diffuse_factor", default=0.15): selector.NumberSelector(
                    {"min": 0.05, "max": 0.5, "mode": "box", "step": 0.01}
                ),
                vol.Required("threshold_direct", default=200): selector.NumberSelector(
                    {"min": 0, "mode": "box"}
                ),
                vol.Required("threshold_diffuse", default=150): selector.NumberSelector(
                    {"min": 0, "mode": "box"}
                ),
                vol.Required("indoor_base", default=23.0): selector.NumberSelector(
                    {"min": 10, "max": 30, "mode": "box", "step": 0.1}
                ),
                vol.Required("outdoor_base", default=19.5): selector.NumberSelector(
                    {"min": 10, "max": 30, "mode": "box", "step": 0.1}
                ),
            }
        )
        return self.async_show_form(
            step_id="global_thresholds",
            data_schema=schema,
            errors={},
        )

    async def async_step_global_scenarios(self, user_input=None):
        """Handle the global scenarios step. Rely on schema for validation."""
        if user_input is not None:
            # Remove deleted sensors if requested
            if user_input.get("delete_weather_warning_sensor"):
                self._user_input.pop("weather_warning_sensor", None)
            if user_input.get("delete_forecast_temperature_sensor"):
                self._user_input.pop("forecast_temperature_sensor", None)
            user_input = {
                k: v
                for k, v in user_input.items()
                if k
                not in [
                    "delete_weather_warning_sensor",
                    "delete_forecast_temperature_sensor",
                ]
            }
            self._user_input.update(user_input)
            self._user_input[CONF_ENTRY_TYPE] = "global"
            return self.async_create_entry(
                title="Global Configuration",
                data={CONF_ENTRY_TYPE: "global"},
                options=self._user_input,
            )
        schema = vol.Schema(
            {
                vol.Required(
                    "scenario_b_temp_indoor_threshold", default=23.5
                ): selector.NumberSelector(
                    {"min": 18, "max": 30, "mode": "box", "step": 0.1}
                ),
                vol.Required(
                    "scenario_b_temp_outdoor_threshold", default=25.5
                ): selector.NumberSelector(
                    {"min": 18, "max": 35, "mode": "box", "step": 0.1}
                ),
                vol.Required(
                    "scenario_c_temp_forecast_threshold", default=28.5
                ): selector.NumberSelector(
                    {"min": 20, "max": 40, "mode": "box", "step": 0.1}
                ),
                vol.Required(
                    "scenario_c_temp_indoor_threshold", default=21.5
                ): selector.NumberSelector(
                    {"min": 18, "max": 30, "mode": "box", "step": 0.1}
                ),
                vol.Required(
                    "scenario_c_temp_outdoor_threshold", default=24.0
                ): selector.NumberSelector(
                    {"min": 18, "max": 35, "mode": "box", "step": 0.1}
                ),
                vol.Required(
                    "scenario_c_start_hour", default=9
                ): selector.NumberSelector(
                    {"min": 0, "max": 23, "mode": "box", "step": 1}
                ),
            }
        )
        return self.async_show_form(
            step_id="global_scenarios",
            data_schema=schema,
            errors={},
        )

    async def async_step_window_init(self, user_input=None):
        return await self.window_flow.async_step_window_init(user_input)

    async def async_step_window_overrides(self, user_input=None):
        return await self.window_flow.async_step_window_overrides(user_input)

    async def async_step_group_init(self, user_input=None):
        """Group-Config: Nur Name und optionale Overrides, keine Fenster-Auswahl mehr. Group wird als eigener Integrationseintrag angelegt."""
        errors = {}
        if user_input is not None:
            user_input[CONF_ENTRY_TYPE] = "group"
            options = {}
            data = {
                k: v for k, v in user_input.items() if k in ("name", CONF_ENTRY_TYPE)
            }
            for k in [
                "threshold_direct",
                "threshold_diffuse",
                "diffuse_factor",
                "indoor_base",
                "outdoor_base",
                "scenario_b_temp_indoor_threshold",
                "scenario_b_temp_outdoor_threshold",
                "scenario_c_temp_forecast_threshold",
                "scenario_c_temp_indoor_threshold",
                "scenario_c_temp_outdoor_threshold",
                "scenario_c_start_hour",
            ]:
                if k in user_input:
                    options[k] = user_input[k]
            # Group wird als eigener Integrationseintrag mit Optionen angelegt
            return self.async_create_entry(
                title=user_input["name"], data=data, options=options
            )

        schema = vol.Schema(
            {
                vol.Required("name"): str,
                vol.Optional("threshold_direct"): selector.NumberSelector(
                    {"min": 0, "mode": "box"}
                ),
                vol.Optional("threshold_diffuse"): selector.NumberSelector(
                    {"min": 0, "mode": "box"}
                ),
                vol.Optional("diffuse_factor"): selector.NumberSelector(
                    {"min": 0.05, "max": 0.5, "mode": "box", "step": 0.01}
                ),
                vol.Optional("indoor_base"): selector.NumberSelector(
                    {"min": 10, "max": 30, "mode": "box", "step": 0.1}
                ),
                vol.Optional("outdoor_base"): selector.NumberSelector(
                    {"min": 10, "max": 30, "mode": "box", "step": 0.1}
                ),
                vol.Optional(
                    "scenario_b_temp_indoor_threshold"
                ): selector.NumberSelector(
                    {"min": 18, "max": 30, "mode": "box", "step": 0.1}
                ),
                vol.Optional(
                    "scenario_b_temp_outdoor_threshold"
                ): selector.NumberSelector(
                    {"min": 18, "max": 35, "mode": "box", "step": 0.1}
                ),
                vol.Optional(
                    "scenario_c_temp_forecast_threshold"
                ): selector.NumberSelector(
                    {"min": 20, "max": 40, "mode": "box", "step": 0.1}
                ),
                vol.Optional(
                    "scenario_c_temp_indoor_threshold"
                ): selector.NumberSelector(
                    {"min": 18, "max": 30, "mode": "box", "step": 0.1}
                ),
                vol.Optional(
                    "scenario_c_temp_outdoor_threshold"
                ): selector.NumberSelector(
                    {"min": 18, "max": 35, "mode": "box", "step": 0.1}
                ),
                vol.Optional("scenario_c_start_hour"): selector.NumberSelector(
                    {"min": 0, "max": 23, "mode": "box", "step": 1}
                ),
            }
        )
        return self.async_show_form(
            step_id="group_init",
            data_schema=schema,
            errors=errors,
            last_step=True,
        )


class SolarWindowOptionsFlowGroup(config_entries.OptionsFlow):
    """Handles options flow for a group entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow for a group entry."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Entry point for the group options flow."""
        errors = {}
        if user_input is not None:
            # Update the config entry's name and title if changed
            new_name = user_input.get("name") or self.config_entry.data.get("name")
            if new_name != self.config_entry.data.get("name"):
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, "name": new_name},
                    title=new_name,
                )
                # Update device name in device registry
                device_registry = dr.async_get(self.hass)
                device = device_registry.async_get_device(
                    {(DOMAIN, self.config_entry.entry_id)}
                )
                if device:
                    device_registry.async_update_device(device.id, name=new_name)
            self.options.update(user_input)
            return self.async_create_entry(title="", data=self.options)

        schema = vol.Schema(
            {
                vol.Required(
                    "name", default=self.config_entry.data.get("name", "")
                ): str,
                vol.Optional("threshold_direct"): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("threshold_diffuse"): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("diffuse_factor"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.05, max=0.5)
                ),
                vol.Optional("indoor_base"): vol.All(
                    vol.Coerce(float), vol.Range(min=10, max=30)
                ),
                vol.Optional("outdoor_base"): vol.All(
                    vol.Coerce(float), vol.Range(min=10, max=30)
                ),
                vol.Optional("scenario_b_temp_indoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_b_temp_outdoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_forecast_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_indoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_outdoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_start_hour"): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=23)
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(schema, self.options)
            if hasattr(self, "add_suggested_values_to_schema")
            else schema,
            errors=errors,
            last_step=True,
        )


class SolarWindowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry
        self._user_input = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Entry point."""
        return await self.async_step_global_init(user_input)

    async def async_step_global_init(self, user_input=None):
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_global_thresholds()

        return self.async_show_form(
            step_id="global_init",
            data_schema=_get_schema(self._user_input),
        )

    async def async_step_global_thresholds(self, user_input=None):
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_global_scenarios()

        options = self._user_input
        return self.async_show_form(
            step_id="global_thresholds",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "g_value", default=options.get("g_value", 0.5)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=0.9)),
                    vol.Required(
                        "frame_width", default=options.get("frame_width", 0.125)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.3)),
                    vol.Required("tilt", default=options.get("tilt", 90)): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=90)
                    ),
                    vol.Required(
                        "diffuse_factor", default=options.get("diffuse_factor", 0.15)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.5)),
                    vol.Required(
                        "threshold_direct", default=options.get("threshold_direct", 200)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                    vol.Required(
                        "threshold_diffuse",
                        default=options.get("threshold_diffuse", 150),
                    ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                    vol.Required(
                        "indoor_base", default=options.get("indoor_base", 23.0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                    vol.Required(
                        "outdoor_base", default=options.get("outdoor_base", 19.5)
                    ): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                }
            ),
        )

    async def async_step_global_scenarios(self, user_input=None):
        if user_input is not None:
            self._user_input.update(user_input)

            if self._user_input.get("delete_weather_warning_sensor"):
                self._user_input.pop("weather_warning_sensor", None)
            if self._user_input.get("delete_forecast_temperature_sensor"):
                self._user_input.pop("forecast_temperature_sensor", None)

            self._user_input.pop("delete_weather_warning_sensor", None)
            self._user_input.pop("delete_forecast_temperature_sensor", None)

            return self.async_create_entry(title="", data=self._user_input)

        options = self._user_input
        return self.async_show_form(
            step_id="global_scenarios",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "scenario_b_temp_indoor_threshold",
                        default=options.get("scenario_b_temp_indoor_threshold", 23.5),
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                    vol.Required(
                        "scenario_b_temp_outdoor_threshold",
                        default=options.get("scenario_b_temp_outdoor_threshold", 25.5),
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                    vol.Required(
                        "scenario_c_temp_forecast_threshold",
                        default=options.get("scenario_c_temp_forecast_threshold", 28.5),
                    ): vol.All(vol.Coerce(float), vol.Range(min=20, max=40)),
                    vol.Required(
                        "scenario_c_temp_indoor_threshold",
                        default=options.get("scenario_c_temp_indoor_threshold", 21.5),
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                    vol.Required(
                        "scenario_c_temp_outdoor_threshold",
                        default=options.get("scenario_c_temp_outdoor_threshold", 24.0),
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                    vol.Required(
                        "scenario_c_start_hour",
                        default=options.get("scenario_c_start_hour", 9),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                }
            ),
        )


class SolarWindowOptionsFlowWindow(config_entries.OptionsFlow):
    """Handle options flow for a window entry."""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize the options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.data)

    async def async_step_init(self, user_input=None):
        """Entry point for the options flow."""
        return await self.async_step_window_init(user_input)

    async def async_step_window_init(self, user_input=None):
        """Manage the options for a window, inkl. Gruppenauswahl."""
        # Find the global configuration entry
        global_entry = next(
            (
                entry
                for entry in self.hass.config_entries.async_entries(DOMAIN)
                if entry.data.get(CONF_ENTRY_TYPE) == "global"
            ),
            None,
        )
        global_defaults = global_entry.options if global_entry else {}
        current_config = self.config_entry.data
        errors = {}

        # Dynamische Gruppenauswahl
        group_entries = [
            entry
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if entry.data.get(CONF_ENTRY_TYPE) == "group"
        ]
        group_names = [
            entry.data.get("name") for entry in group_entries if entry.data.get("name")
        ]
        group_select = vol.Optional("group", default=current_config.get("group"))
        if group_names:
            group_field = group_select if group_names else None
        else:
            group_field = group_select

        required_fields = ["name", "azimuth", "width", "height"]

        if user_input is not None:
            # Check for missing required fields
            for field in required_fields:
                if user_input.get(field) in (None, ""):
                    errors[field] = "required"
            # EntitySelector required field
            if user_input.get("room_temp_entity") in (None, ""):
                errors["room_temp_entity"] = "required_entity"

            # Validation logic
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
                self.options.update(user_input)
                return await self.async_step_window_overrides()

        # Merge global defaults with current window config to pre-fill the form
        options = {**global_defaults, **current_config}

        schema_dict = {
            vol.Required("name"): str,
            vol.Required("azimuth"): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=360)
            ),
            vol.Optional("azimuth_min"): vol.All(
                vol.Coerce(float), vol.Range(min=-90, max=0)
            ),
            vol.Optional("azimuth_max"): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=90)
            ),
            vol.Optional("elevation_min"): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=90)
            ),
            vol.Optional("elevation_max"): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=90)
            ),
            vol.Required("width"): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=10)
            ),
            vol.Required("height"): vol.All(
                vol.Coerce(float), vol.Range(min=0.1, max=10)
            ),
            vol.Optional("shadow_depth"): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=5)
            ),
            vol.Optional("shadow_offset"): vol.All(
                vol.Coerce(float), vol.Range(min=0, max=5)
            ),
            vol.Required("room_temp_entity"): selector.EntitySelector(
                {"domain": "sensor", "device_class": "temperature"}
            ),
        }
        # Gruppenauswahl als Dropdown (falls Gruppen vorhanden)
        current_group = current_config.get("group")
        # Hole das Label aus den Translations
        translations = self.hass.data.get(
            "custom_components.solar_window_system.translations", {}
        )
        no_group_label = translations.get("no_group", "No group assigned")
        if group_names:
            if current_group:
                # Wenn eine Gruppe zugeordnet ist, biete die Option zum Entfernen an
                # sowie alle verfügbaren Gruppen
                group_choices = {name: name for name in group_names}
                group_choices[None] = no_group_label
                default_group = current_group if current_group in group_names else None
                schema_dict[vol.Optional("group", default=default_group)] = vol.In(
                    group_choices
                )
                self._group_labels = {None: no_group_label}
            else:
                # Wenn keine Gruppe zugeordnet ist, nur die vorhandenen Gruppen anzeigen
                # (ohne None Option)
                schema_dict[vol.Optional("group")] = vol.In(group_names)
                self._group_labels = {}
        else:
            schema_dict[vol.Optional("group")] = str

        schema = vol.Schema(schema_dict)

        # Use the name from user_input if available, else from config/data
        window_name = (
            (user_input or {}).get("name")
            or options.get("name")
            or self.config_entry.data.get("name")
            or "Unknown Window"
        )

        return self.async_show_form(
            step_id="window_init",
            data_schema=self.add_suggested_values_to_schema(schema, options),
            errors=errors,
            description_placeholders={
                "tilt": str(global_defaults.get("tilt", 90)),
                "g_value": str(global_defaults.get("g_value", 0.5)),
                "frame_width": str(global_defaults.get("frame_width", 0.125)),
                "name": window_name,
            },
        )

    async def async_step_window_overrides(self, user_input=None):
        """Manage the override options for a window."""
        global_entry = next(
            (
                entry
                for entry in self.hass.config_entries.async_entries(DOMAIN)
                if entry.data.get(CONF_ENTRY_TYPE) == "global"
            ),
            None,
        )
        global_defaults = global_entry.options if global_entry else {}

        if user_input is not None:
            # Gruppenauswahl: Nur wenn explizit None gewählt wurde,
            # entferne die Gruppenzuordnung
            if "group" in user_input:
                if user_input["group"] is None:
                    self.options.pop("group", None)
                    user_input = {k: v for k, v in user_input.items() if k != "group"}
                else:
                    self.options["group"] = user_input["group"]
                # Entferne group aus user_input, damit es nicht nochmal
                # überschrieben wird
                user_input = {k: v for k, v in user_input.items() if k != "group"}
            self.options.update(user_input)

            # Remove keys that are same as global or are empty/None
            for key in list(self.options.keys()):
                if key in [CONF_ENTRY_TYPE, CONF_WINDOW_NAME]:
                    continue

                if (
                    key in global_defaults
                    and self.options.get(key) == global_defaults[key]
                ) or self.options.get(key) in [None, ""]:
                    del self.options[key]

            # Update the config entry with the new data and update
            # the title if name changed
            new_title = self.options.get("name") or self.config_entry.title
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=self.options, title=new_title
            )
            # Reload the integration to apply changes
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            # Finish the flow
            return self.async_create_entry(title="", data={})

        # Merge global defaults with current window config to pre-fill the form
        options = {**global_defaults, **self.options}

        schema = vol.Schema(
            {
                vol.Optional("diffuse_factor"): vol.All(
                    vol.Coerce(float), vol.Range(min=0.05, max=0.5)
                ),
                vol.Optional("threshold_direct"): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("threshold_diffuse"): vol.All(
                    vol.Coerce(float), vol.Range(min=0)
                ),
                vol.Optional("indoor_base"): vol.All(
                    vol.Coerce(float), vol.Range(min=10, max=30)
                ),
                vol.Optional("outdoor_base"): vol.All(
                    vol.Coerce(float), vol.Range(min=10, max=30)
                ),
                vol.Optional("scenario_b_temp_indoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_b_temp_outdoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_forecast_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_indoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_temp_outdoor_threshold"): vol.Coerce(float),
                vol.Optional("scenario_c_start_hour"): vol.All(
                    vol.Coerce(int), vol.Range(min=0, max=23)
                ),
            }
        )

        # Use the name from options or config_entry for placeholder
        window_name = (
            options.get("name")
            or self.config_entry.data.get("name")
            or "Unknown Window"
        )
        return self.async_show_form(
            step_id="window_overrides",
            data_schema=self.add_suggested_values_to_schema(schema, options),
            last_step=True,
            description_placeholders={
                "name": window_name,
            },
        )
