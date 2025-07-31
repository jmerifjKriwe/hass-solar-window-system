"""Config flow for Solar Window System."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import (
    DOMAIN,
    CONF_ENTRY_TYPE,
    CONF_WINDOW_NAME,
    CONF_AZIMUTH,
    CONF_AZIMUTH_RANGE,
    CONF_ELEVATION_RANGE,
    CONF_WIDTH,
    CONF_HEIGHT,
    CONF_SHADOW_DEPTH,
    CONF_SHADOW_OFFSET,
    CONF_ROOM_TEMP_ENTITY,
    CONF_GROUP_NAME,
)


class SolarWindowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Solar Window System."""

    VERSION = 1
    _user_input = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        if user_input is not None:
            entry_type = user_input[CONF_ENTRY_TYPE]
            if entry_type == "global":
                return await self.async_step_global()
            elif entry_type == "window":
                return await self.async_step_add_window()
            elif entry_type == "group":
                return await self.async_step_add_group()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_ENTRY_TYPE): vol.In(["global", "window", "group"])
            })
        )

    async def async_step_global(self, user_input=None):
        """Handle the global configuration step."""
        if user_input is not None:
            self._user_input.update(user_input)
            return self.async_create_entry(
                title="Global Configuration", data={}, options=self._user_input
            )

        return self.async_show_form(
            step_id="global",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "solar_radiation_sensor",
                        default=self.hass.config.get("solar_radiation_sensor"),
                    ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                    vol.Required(
                        "outdoor_temperature_sensor",
                        default=self.hass.config.get("outdoor_temperature_sensor"),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
                    ),
                    vol.Required(
                        "update_interval", default=5
                    ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                    vol.Required(
                        "min_solar_radiation", default=50
                    ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                    vol.Required(
                        "min_sun_elevation", default=10
                    ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
                    vol.Optional(
                        "weather_warning_sensor",
                        default=self.hass.config.get("weather_warning_sensor"),
                    ): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
                    vol.Optional(
                        "forecast_temperature_sensor",
                        default=self.hass.config.get("forecast_temperature_sensor"),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
                    ),
                    vol.Required("g_value", default=0.5): vol.All(
                        vol.Coerce(float), vol.Range(min=0.1, max=0.9)
                    ),
                    vol.Required("frame_width", default=0.125): vol.All(
                        vol.Coerce(float), vol.Range(min=0.05, max=0.3)
                    ),
                    vol.Required("tilt", default=90): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=90)
                    ),
                    vol.Required("diffuse_factor", default=0.15): vol.All(
                        vol.Coerce(float), vol.Range(min=0.05, max=0.5)
                    ),
                    vol.Required("threshold_direct", default=200): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Required("threshold_diffuse", default=150): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Required("indoor_base", default=23.0): vol.All(
                        vol.Coerce(float), vol.Range(min=10, max=30)
                    ),
                    vol.Required("outdoor_base", default=19.5): vol.All(
                        vol.Coerce(float), vol.Range(min=10, max=30)
                    ),
                    vol.Required(
                        "scenario_b_temp_indoor_threshold", default=23.5
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                    vol.Required(
                        "scenario_b_temp_outdoor_threshold", default=25.5
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                    vol.Required(
                        "scenario_c_temp_forecast_threshold", default=28.5
                    ): vol.All(vol.Coerce(float), vol.Range(min=20, max=40)),
                    vol.Required(
                        "scenario_c_temp_indoor_threshold", default=21.5
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                    vol.Required(
                        "scenario_c_temp_outdoor_threshold", default=24.0
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                    vol.Required("scenario_c_start_hour", default=9): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=23)
                    ),
                }
            ),
        )

    async def async_step_add_window(self, user_input=None):
        """Handle adding a new window configuration."""
        if user_input is not None:
            self._user_input.update(user_input)
            return await self.async_step_window_overrides()

        return self.async_show_form(
            step_id="add_window",
            data_schema=vol.Schema({
                vol.Required(CONF_WINDOW_NAME): str,
                vol.Required(CONF_AZIMUTH): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
                vol.Required(CONF_AZIMUTH_RANGE): vol.All(vol.Coerce(list), [vol.Coerce(float)]),
                vol.Required(CONF_ELEVATION_RANGE): vol.All(vol.Coerce(list), [vol.Coerce(float)]),
                vol.Required(CONF_WIDTH): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(CONF_HEIGHT): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(CONF_SHADOW_DEPTH): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(CONF_SHADOW_OFFSET): vol.All(vol.Coerce(float)),
                vol.Required(CONF_ROOM_TEMP_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="temperature")),
                vol.Optional("tilt", default=90): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
                vol.Optional("g_value", default=0.5): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=0.9)),
                vol.Optional("frame_width", default=0.125): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.3)),
            })
        )

    async def async_step_window_overrides(self, user_input=None):
        """Handle optional window override settings."""
        if user_input is not None:
            self._user_input.update(user_input)
            return self.async_create_entry(
                title=f"Fenster: {self._user_input.get(CONF_WINDOW_NAME, 'Unnamed Window')}",
                data=self._user_input,
            )

        return self.async_show_form(
            step_id="window_overrides",
            data_schema=vol.Schema({
                vol.Optional("diffuse_factor", default=0.15): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.5)),
                vol.Optional("threshold_direct", default=200): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional("threshold_diffuse", default=150): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional("indoor_base", default=23.0): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Optional("outdoor_base", default=19.5): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Optional("scenario_b_temp_indoor_threshold", default=23.5): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                vol.Optional("scenario_b_temp_outdoor_threshold", default=25.5): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                vol.Optional("scenario_c_temp_forecast_threshold", default=28.5): vol.All(vol.Coerce(float), vol.Range(min=20, max=40)),
                vol.Optional("scenario_c_temp_indoor_threshold", default=21.5): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                vol.Optional("scenario_c_temp_outdoor_threshold", default=24.0): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                vol.Optional("scenario_c_start_hour", default=9): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            })
        )

    async def async_step_add_group(self, user_input=None):
        """Handle adding a new group configuration."""
        if user_input is not None:
            self._user_input.update(user_input)
            return self.async_create_entry(
                title=f"Gruppe: {self._user_input.get(CONF_GROUP_NAME, 'Unnamed Group')}",
                data=self._user_input,
            )

        return self.async_show_form(
            step_id="add_group",
            data_schema=vol.Schema({
                vol.Required(CONF_GROUP_NAME): str,
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow handler for this config entry."""
        flow = SolarWindowOptionsFlowHandler()
        flow._config_entry = config_entry
        return flow


class SolarWindowOptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry
        self._user_input = {}

    async def async_step_init(self, user_input=None):
        """Manage the first step of the options flow."""
        if user_input is not None:
            self._user_input.update(user_input)
            return self.async_create_entry(title="", data=self._user_input)

        # Determine schema based on entry type
        entry_type = self.config_entry.data.get(CONF_ENTRY_TYPE)
        schema = vol.Schema({})

        if entry_type == "global":
            schema = vol.Schema(
                {
                    vol.Required(
                        "solar_radiation_sensor",
                        default=self.config_entry.options.get("solar_radiation_sensor"),
                    ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                    vol.Required(
                        "outdoor_temperature_sensor",
                        default=self.config_entry.options.get("outdoor_temperature_sensor"),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
                    ),
                    vol.Required(
                        "update_interval", default=self.config_entry.options.get("update_interval", 5)
                    ): vol.All(vol.Coerce(int), vol.Range(min=1)),
                    vol.Required(
                        "min_solar_radiation", default=self.config_entry.options.get("min_solar_radiation", 50)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0)),
                    vol.Required(
                        "min_sun_elevation", default=self.config_entry.options.get("min_sun_elevation", 10)
                    ): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
                    vol.Optional(
                        "weather_warning_sensor",
                        default=self.config_entry.options.get("weather_warning_sensor"),
                    ): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
                    vol.Optional(
                        "forecast_temperature_sensor",
                        default=self.config_entry.options.get("forecast_temperature_sensor"),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
                    ),
                    vol.Required("g_value", default=self.config_entry.options.get("g_value", 0.5)): vol.All(
                        vol.Coerce(float), vol.Range(min=0.1, max=0.9)
                    ),
                    vol.Required("frame_width", default=self.config_entry.options.get("frame_width", 0.125)): vol.All(
                        vol.Coerce(float), vol.Range(min=0.05, max=0.3)
                    ),
                    vol.Required("tilt", default=self.config_entry.options.get("tilt", 90)): vol.All(
                        vol.Coerce(float), vol.Range(min=0, max=90)
                    ),
                    vol.Required("diffuse_factor", default=self.config_entry.options.get("diffuse_factor", 0.15)): vol.All(
                        vol.Coerce(float), vol.Range(min=0.05, max=0.5)
                    ),
                    vol.Required("threshold_direct", default=self.config_entry.options.get("threshold_direct", 200)): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Required("threshold_diffuse", default=self.config_entry.options.get("threshold_diffuse", 150)): vol.All(
                        vol.Coerce(float), vol.Range(min=0)
                    ),
                    vol.Required("indoor_base", default=self.config_entry.options.get("indoor_base", 23.0)): vol.All(
                        vol.Coerce(float), vol.Range(min=10, max=30)
                    ),
                    vol.Required("outdoor_base", default=self.config_entry.options.get("outdoor_base", 19.5)): vol.All(
                        vol.Coerce(float), vol.Range(min=10, max=30)
                    ),
                    vol.Required(
                        "scenario_b_temp_indoor_threshold", default=self.config_entry.options.get("scenario_b_temp_indoor_threshold", 23.5)
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                    vol.Required(
                        "scenario_b_temp_outdoor_threshold", default=self.config_entry.options.get("scenario_b_temp_outdoor_threshold", 25.5)
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                    vol.Required(
                        "scenario_c_temp_forecast_threshold", default=self.config_entry.options.get("scenario_c_temp_forecast_threshold", 28.5)
                    ): vol.All(vol.Coerce(float), vol.Range(min=20, max=40)),
                    vol.Required(
                        "scenario_c_temp_indoor_threshold", default=self.config_entry.options.get("scenario_c_temp_indoor_threshold", 21.5)
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                    vol.Required(
                        "scenario_c_temp_outdoor_threshold", default=self.config_entry.options.get("scenario_c_temp_outdoor_threshold", 24.0)
                    ): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                    vol.Required("scenario_c_start_hour", default=self.config_entry.options.get("scenario_c_start_hour", 9)): vol.All(
                        vol.Coerce(int), vol.Range(min=0, max=23)
                    ),
                }
            )
        elif entry_type == "window":
            schema = vol.Schema({
                vol.Required(CONF_WINDOW_NAME, default=self.config_entry.options.get(CONF_WINDOW_NAME)): str,
                vol.Required(CONF_AZIMUTH, default=self.config_entry.options.get(CONF_AZIMUTH)): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
                vol.Required(CONF_AZIMUTH_RANGE, default=self.config_entry.options.get(CONF_AZIMUTH_RANGE)): vol.All(vol.Coerce(list), [vol.Coerce(float)]),
                vol.Required(CONF_ELEVATION_RANGE, default=self.config_entry.options.get(CONF_ELEVATION_RANGE)): vol.All(vol.Coerce(list), [vol.Coerce(float)]),
                vol.Required(CONF_WIDTH, default=self.config_entry.options.get(CONF_WIDTH)): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(CONF_HEIGHT, default=self.config_entry.options.get(CONF_HEIGHT)): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(CONF_SHADOW_DEPTH, default=self.config_entry.options.get(CONF_SHADOW_DEPTH)): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Required(CONF_SHADOW_OFFSET, default=self.config_entry.options.get(CONF_SHADOW_OFFSET)): vol.All(vol.Coerce(float)),
                vol.Required(CONF_ROOM_TEMP_ENTITY, default=self.config_entry.options.get(CONF_ROOM_TEMP_ENTITY)): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class="temperature")),
                vol.Optional("tilt", default=self.config_entry.options.get("tilt", 90)): vol.All(vol.Coerce(float), vol.Range(min=0, max=90)),
                vol.Optional("g_value", default=self.config_entry.options.get("g_value", 0.5)): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=0.9)),
                vol.Optional("frame_width", default=self.config_entry.options.get("frame_width", 0.125)): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.3)),
                vol.Optional("diffuse_factor", default=self.config_entry.options.get("diffuse_factor", 0.15)): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.5)),
                vol.Optional("threshold_direct", default=self.config_entry.options.get("threshold_direct", 200)): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional("threshold_diffuse", default=self.config_entry.options.get("threshold_diffuse", 150)): vol.All(vol.Coerce(float), vol.Range(min=0)),
                vol.Optional("indoor_base", default=self.config_entry.options.get("indoor_base", 23.0)): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Optional("outdoor_base", default=self.config_entry.options.get("outdoor_base", 19.5)): vol.All(vol.Coerce(float), vol.Range(min=10, max=30)),
                vol.Optional("scenario_b_temp_indoor_threshold", default=self.config_entry.options.get("scenario_b_temp_indoor_threshold", 23.5)): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                vol.Optional("scenario_b_temp_outdoor_threshold", default=self.config_entry.options.get("scenario_b_temp_outdoor_threshold", 25.5)): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                vol.Optional("scenario_c_temp_forecast_threshold", default=self.config_entry.options.get("scenario_c_temp_forecast_threshold", 28.5)): vol.All(vol.Coerce(float), vol.Range(min=20, max=40)),
                vol.Optional("scenario_c_temp_indoor_threshold", default=self.config_entry.options.get("scenario_c_temp_indoor_threshold", 21.5)): vol.All(vol.Coerce(float), vol.Range(min=18, max=30)),
                vol.Optional("scenario_c_temp_outdoor_threshold", default=self.config_entry.options.get("scenario_c_temp_outdoor_threshold", 24.0)): vol.All(vol.Coerce(float), vol.Range(min=18, max=35)),
                vol.Optional("scenario_c_start_hour", default=self.config_entry.options.get("scenario_c_start_hour", 9)): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
            })
        elif entry_type == "group":
            schema = vol.Schema({
                vol.Required(CONF_GROUP_NAME, default=self.config_entry.options.get(CONF_GROUP_NAME)): str,
            })

        return self.async_show_form(
            step_id="init", data_schema=schema
        )
