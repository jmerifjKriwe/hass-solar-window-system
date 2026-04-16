"""Config flow for Solar Window System integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_AZIMUTH,
    CONF_FRAME_WIDTH,
    CONF_G_VALUE,
    CONF_GEOMETRY,
    CONF_GROUP_ID,
    CONF_GROUP_TYPE,
    CONF_HEIGHT,
    CONF_IRRADIANCE_DIFFUSE_SENSOR,
    CONF_IRRADIANCE_SENSOR,
    CONF_PROPERTIES,
    CONF_SENSORS,
    CONF_SHADING_DEPTH,
    CONF_TEMP_INDOOR,
    CONF_TEMP_OUTDOOR,
    CONF_TILT,
    CONF_USE_IRRADIANCE_DIFFUSE,
    CONF_USE_TEMP_INDOOR,
    CONF_USE_TEMP_OUTDOOR,
    CONF_USE_WEATHER_CONDITION,
    CONF_USE_WEATHER_WARNING,
    CONF_VISIBLE_AZIMUTH_END,
    CONF_VISIBLE_AZIMUTH_START,
    CONF_WEATHER_CONDITION,
    CONF_WEATHER_WARNING,
    CONF_WIDTH,
    CONF_WINDOW_RECESS,
    DEFAULT_FORECAST_HIGH,
    DEFAULT_FRAME_WIDTH,
    DEFAULT_G_VALUE,
    DEFAULT_INSIDE_TEMP,
    DEFAULT_OUTSIDE_TEMP,
    DEFAULT_SHADING_DEPTH,
    DEFAULT_SOLAR_ENERGY,
    DEFAULT_WINDOW_RECESS,
    DOMAIN,
    GROUP_TYPE_ORIENTATION,
    GROUP_TYPE_ROOM,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Solar Window System"

# Subentry types
SUBENTRY_TYPE_WINDOW = "window"
SUBENTRY_TYPE_GROUP = "group"


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    _ = hass
    return {"title": data["name"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solar Window System."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step - global sensor configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store global config and proceed to menu
            return self.async_create_entry(
                title=user_input["name"],
                data={
                    "name": user_input["name"],
                    CONF_SENSORS: {
                        CONF_IRRADIANCE_SENSOR: user_input.get(CONF_IRRADIANCE_SENSOR),
                        CONF_IRRADIANCE_DIFFUSE_SENSOR: user_input.get(
                            CONF_IRRADIANCE_DIFFUSE_SENSOR
                        ),
                        CONF_TEMP_OUTDOOR: user_input.get(CONF_TEMP_OUTDOOR),
                        CONF_TEMP_INDOOR: user_input.get(CONF_TEMP_INDOOR),
                        CONF_WEATHER_WARNING: user_input.get(CONF_WEATHER_WARNING),
                        CONF_WEATHER_CONDITION: user_input.get(CONF_WEATHER_CONDITION),
                    },
                    CONF_PROPERTIES: {
                        CONF_G_VALUE: user_input.get(CONF_G_VALUE, DEFAULT_G_VALUE),
                        CONF_FRAME_WIDTH: user_input.get(CONF_FRAME_WIDTH, DEFAULT_FRAME_WIDTH),
                        CONF_WINDOW_RECESS: user_input.get(
                            CONF_WINDOW_RECESS, DEFAULT_WINDOW_RECESS
                        ),
                        CONF_SHADING_DEPTH: user_input.get(
                            CONF_SHADING_DEPTH, DEFAULT_SHADING_DEPTH
                        ),
                    },
                },
            )

        data_schema = vol.Schema(
            {
                vol.Required("name", default=DEFAULT_NAME): TextSelector(),
                vol.Required(CONF_IRRADIANCE_SENSOR): EntitySelector(
                    EntitySelectorConfig(device_class="irradiance")
                ),
                vol.Optional(CONF_IRRADIANCE_DIFFUSE_SENSOR): EntitySelector(
                    EntitySelectorConfig(device_class="irradiance")
                ),
                vol.Optional(CONF_TEMP_OUTDOOR): EntitySelector(
                    EntitySelectorConfig(device_class="temperature")
                ),
                vol.Optional(CONF_TEMP_INDOOR): EntitySelector(
                    EntitySelectorConfig(device_class="temperature")
                ),
                vol.Optional(CONF_WEATHER_WARNING): EntitySelector(
                    EntitySelectorConfig(domain="binary_sensor")
                ),
                vol.Optional(CONF_WEATHER_CONDITION): EntitySelector(),
                vol.Required(
                    CONF_PROPERTIES,
                    default={
                        CONF_G_VALUE: DEFAULT_G_VALUE,
                        CONF_FRAME_WIDTH: DEFAULT_FRAME_WIDTH,
                        CONF_WINDOW_RECESS: DEFAULT_WINDOW_RECESS,
                        CONF_SHADING_DEPTH: DEFAULT_SHADING_DEPTH,
                    },
                ): section(  # type: ignore[no-untyped-call]
                    vol.Schema(
                        {
                            vol.Optional(CONF_G_VALUE, default=DEFAULT_G_VALUE): NumberSelector(
                                NumberSelectorConfig(min=0.1, max=1.0, step=0.05)
                            ),
                            vol.Optional(
                                CONF_FRAME_WIDTH, default=DEFAULT_FRAME_WIDTH
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=20, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(
                                CONF_WINDOW_RECESS, default=DEFAULT_WINDOW_RECESS
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=100, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(
                                CONF_SHADING_DEPTH, default=DEFAULT_SHADING_DEPTH
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=200, step=1, unit_of_measurement="cm"
                                )
                            ),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: config_entries.ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return subentries supported by this integration."""
        return {
            SUBENTRY_TYPE_WINDOW: WindowSubentryFlowHandler,
            SUBENTRY_TYPE_GROUP: GroupSubentryFlowHandler,
        }

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration of the integration."""
        entry = self._get_reconfigure_entry()

        def _is_valid_entity_id(value: Any) -> bool:
            """Check if value is a valid entity ID (not None and not empty string)."""
            return value is not None and value != ""

        _LOGGER.warning("DEBUG reconfigure: user_input=%s", user_input)
        _LOGGER.warning("DEBUG reconfigure: entry.data=%s", entry.data)

        if user_input is not None:
            errors: dict[str, str] = {}

            # Validate: If checkbox is set, entity must also be set
            if user_input.get(CONF_USE_IRRADIANCE_DIFFUSE) and not _is_valid_entity_id(
                user_input.get(CONF_IRRADIANCE_DIFFUSE_SENSOR)
            ):
                errors[CONF_IRRADIANCE_DIFFUSE_SENSOR] = "missing_entity_for_enabled_sensor"

            if user_input.get(CONF_USE_TEMP_OUTDOOR) and not _is_valid_entity_id(
                user_input.get(CONF_TEMP_OUTDOOR)
            ):
                errors[CONF_TEMP_OUTDOOR] = "missing_entity_for_enabled_sensor"

            if user_input.get(CONF_USE_TEMP_INDOOR) and not _is_valid_entity_id(
                user_input.get(CONF_TEMP_INDOOR)
            ):
                errors[CONF_TEMP_INDOOR] = "missing_entity_for_enabled_sensor"

            if user_input.get(CONF_USE_WEATHER_WARNING) and not _is_valid_entity_id(
                user_input.get(CONF_WEATHER_WARNING)
            ):
                errors[CONF_WEATHER_WARNING] = "missing_entity_for_enabled_sensor"

            if user_input.get(CONF_USE_WEATHER_CONDITION) and not _is_valid_entity_id(
                user_input.get(CONF_WEATHER_CONDITION)
            ):
                errors[CONF_WEATHER_CONDITION] = "missing_entity_for_enabled_sensor"

            if errors:
                # Show form again with errors
                sensors = entry.data.get(CONF_SENSORS, {})
                properties = entry.data.get(CONF_PROPERTIES, {})
                data_schema = self._build_reconfigure_schema(entry, sensors, properties)
                return self.async_show_form(
                    step_id="reconfigure",
                    data_schema=self.add_suggested_values_to_schema(data_schema, user_input),
                    errors=errors,
                )

            # Build sensors dict - only include sensors if checkbox is checked AND entity is valid
            sensors = {}
            # Required sensor: always include if valid
            if _is_valid_entity_id(user_input.get(CONF_IRRADIANCE_SENSOR)):
                sensors[CONF_IRRADIANCE_SENSOR] = user_input[CONF_IRRADIANCE_SENSOR]

            # Optional sensors: only include if checkbox is checked AND entity is valid
            if user_input.get(CONF_USE_IRRADIANCE_DIFFUSE) and _is_valid_entity_id(
                user_input.get(CONF_IRRADIANCE_DIFFUSE_SENSOR)
            ):
                sensors[CONF_IRRADIANCE_DIFFUSE_SENSOR] = user_input[CONF_IRRADIANCE_DIFFUSE_SENSOR]

            if user_input.get(CONF_USE_TEMP_OUTDOOR) and _is_valid_entity_id(
                user_input.get(CONF_TEMP_OUTDOOR)
            ):
                sensors[CONF_TEMP_OUTDOOR] = user_input[CONF_TEMP_OUTDOOR]

            if user_input.get(CONF_USE_TEMP_INDOOR) and _is_valid_entity_id(
                user_input.get(CONF_TEMP_INDOOR)
            ):
                sensors[CONF_TEMP_INDOOR] = user_input[CONF_TEMP_INDOOR]

            if user_input.get(CONF_USE_WEATHER_WARNING) and _is_valid_entity_id(
                user_input.get(CONF_WEATHER_WARNING)
            ):
                sensors[CONF_WEATHER_WARNING] = user_input[CONF_WEATHER_WARNING]

            if user_input.get(CONF_USE_WEATHER_CONDITION) and _is_valid_entity_id(
                user_input.get(CONF_WEATHER_CONDITION)
            ):
                sensors[CONF_WEATHER_CONDITION] = user_input[CONF_WEATHER_CONDITION]

            # Update the entry data - include checkbox states separately
            data_updates = {
                "name": user_input["name"],
                CONF_SENSORS: sensors,
                CONF_USE_IRRADIANCE_DIFFUSE: user_input.get(CONF_USE_IRRADIANCE_DIFFUSE, False),
                CONF_USE_TEMP_OUTDOOR: user_input.get(CONF_USE_TEMP_OUTDOOR, False),
                CONF_USE_TEMP_INDOOR: user_input.get(CONF_USE_TEMP_INDOOR, False),
                CONF_USE_WEATHER_WARNING: user_input.get(CONF_USE_WEATHER_WARNING, False),
                CONF_USE_WEATHER_CONDITION: user_input.get(CONF_USE_WEATHER_CONDITION, False),
                CONF_PROPERTIES: {
                    CONF_G_VALUE: user_input[CONF_PROPERTIES].get(CONF_G_VALUE, DEFAULT_G_VALUE),
                    CONF_FRAME_WIDTH: user_input[CONF_PROPERTIES].get(
                        CONF_FRAME_WIDTH, DEFAULT_FRAME_WIDTH
                    ),
                    CONF_WINDOW_RECESS: user_input[CONF_PROPERTIES].get(
                        CONF_WINDOW_RECESS, DEFAULT_WINDOW_RECESS
                    ),
                    CONF_SHADING_DEPTH: user_input[CONF_PROPERTIES].get(
                        CONF_SHADING_DEPTH, DEFAULT_SHADING_DEPTH
                    ),
                },
            }
            return self.async_update_reload_and_abort(entry, data_updates=data_updates)

        # Pre-fill with existing data
        sensors = entry.data.get(CONF_SENSORS, {})
        properties = entry.data.get(CONF_PROPERTIES, {})
        data_schema = self._build_reconfigure_schema(entry, sensors, properties)

        # Build suggested values from existing config
        # Checkbox states are stored directly in entry.data, derive from sensor existence if not set
        suggested_values = {
            "name": entry.data.get("name"),
            CONF_IRRADIANCE_SENSOR: sensors.get(CONF_IRRADIANCE_SENSOR),
            CONF_USE_IRRADIANCE_DIFFUSE: entry.data.get(
                CONF_USE_IRRADIANCE_DIFFUSE,
                sensors.get(CONF_IRRADIANCE_DIFFUSE_SENSOR) not in (None, ""),
            ),
            CONF_IRRADIANCE_DIFFUSE_SENSOR: sensors.get(CONF_IRRADIANCE_DIFFUSE_SENSOR),
            CONF_USE_TEMP_OUTDOOR: entry.data.get(
                CONF_USE_TEMP_OUTDOOR, sensors.get(CONF_TEMP_OUTDOOR) not in (None, "")
            ),
            CONF_TEMP_OUTDOOR: sensors.get(CONF_TEMP_OUTDOOR),
            CONF_USE_TEMP_INDOOR: entry.data.get(
                CONF_USE_TEMP_INDOOR, sensors.get(CONF_TEMP_INDOOR) not in (None, "")
            ),
            CONF_TEMP_INDOOR: sensors.get(CONF_TEMP_INDOOR),
            CONF_USE_WEATHER_WARNING: entry.data.get(
                CONF_USE_WEATHER_WARNING, sensors.get(CONF_WEATHER_WARNING) not in (None, "")
            ),
            CONF_WEATHER_WARNING: sensors.get(CONF_WEATHER_WARNING),
            CONF_USE_WEATHER_CONDITION: entry.data.get(
                CONF_USE_WEATHER_CONDITION, sensors.get(CONF_WEATHER_CONDITION) not in (None, "")
            ),
            CONF_WEATHER_CONDITION: sensors.get(CONF_WEATHER_CONDITION),
            CONF_PROPERTIES: properties,
        }

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(data_schema, suggested_values),
        )

    def _build_reconfigure_schema(
        self,
        entry: config_entries.ConfigEntry,
        sensors: dict[str, Any],
        properties: dict[str, Any],
    ) -> vol.Schema:
        """Build the schema for reconfigure with checkboxes for optional sensors."""
        return vol.Schema(
            {
                vol.Required("name", default=entry.data.get("name", DEFAULT_NAME)): TextSelector(),
                vol.Required(
                    CONF_IRRADIANCE_SENSOR,
                    default=sensors.get(CONF_IRRADIANCE_SENSOR),
                ): EntitySelector(EntitySelectorConfig(device_class="irradiance")),
                # Irradiance diffuse sensor with checkbox
                vol.Optional(
                    CONF_USE_IRRADIANCE_DIFFUSE,
                    default=sensors.get(CONF_IRRADIANCE_DIFFUSE_SENSOR) not in (None, ""),
                ): BooleanSelector(),
                vol.Optional(CONF_IRRADIANCE_DIFFUSE_SENSOR): vol.Any(
                    None, EntitySelector(EntitySelectorConfig(device_class="irradiance"))
                ),
                # Outdoor temp sensor with checkbox
                vol.Optional(
                    CONF_USE_TEMP_OUTDOOR,
                    default=sensors.get(CONF_TEMP_OUTDOOR) not in (None, ""),
                ): BooleanSelector(),
                vol.Optional(CONF_TEMP_OUTDOOR): vol.Any(
                    None, EntitySelector(EntitySelectorConfig(device_class="temperature"))
                ),
                # Indoor temp sensor with checkbox
                vol.Optional(
                    CONF_USE_TEMP_INDOOR,
                    default=sensors.get(CONF_TEMP_INDOOR) not in (None, ""),
                ): BooleanSelector(),
                vol.Optional(CONF_TEMP_INDOOR): vol.Any(
                    None, EntitySelector(EntitySelectorConfig(device_class="temperature"))
                ),
                # Weather warning sensor with checkbox
                vol.Optional(
                    CONF_USE_WEATHER_WARNING,
                    default=sensors.get(CONF_WEATHER_WARNING) not in (None, ""),
                ): BooleanSelector(),
                vol.Optional(CONF_WEATHER_WARNING): vol.Any(
                    None, EntitySelector(EntitySelectorConfig(domain="binary_sensor"))
                ),
                # Weather condition sensor with checkbox
                vol.Optional(
                    CONF_USE_WEATHER_CONDITION,
                    default=sensors.get(CONF_WEATHER_CONDITION) not in (None, ""),
                ): BooleanSelector(),
                vol.Optional(CONF_WEATHER_CONDITION): vol.Any(None, EntitySelector()),
                vol.Optional(
                    CONF_PROPERTIES,
                    default={
                        CONF_G_VALUE: properties.get(CONF_G_VALUE, DEFAULT_G_VALUE),
                        CONF_FRAME_WIDTH: properties.get(CONF_FRAME_WIDTH, DEFAULT_FRAME_WIDTH),
                        CONF_WINDOW_RECESS: properties.get(
                            CONF_WINDOW_RECESS, DEFAULT_WINDOW_RECESS
                        ),
                        CONF_SHADING_DEPTH: properties.get(
                            CONF_SHADING_DEPTH, DEFAULT_SHADING_DEPTH
                        ),
                    },
                ): section(  # type: ignore[no-untyped-call]
                    vol.Schema(
                        {
                            vol.Optional(
                                CONF_G_VALUE,
                                default=properties.get(CONF_G_VALUE, DEFAULT_G_VALUE),
                            ): NumberSelector(NumberSelectorConfig(min=0.1, max=1.0, step=0.05)),
                            vol.Optional(
                                CONF_FRAME_WIDTH,
                                default=properties.get(CONF_FRAME_WIDTH, DEFAULT_FRAME_WIDTH),
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=20, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(
                                CONF_WINDOW_RECESS,
                                default=properties.get(CONF_WINDOW_RECESS, DEFAULT_WINDOW_RECESS),
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=100, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(
                                CONF_SHADING_DEPTH,
                                default=properties.get(CONF_SHADING_DEPTH, DEFAULT_SHADING_DEPTH),
                            ): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=200, step=1, unit_of_measurement="cm"
                                )
                            ),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )


class WindowSubentryFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for adding/modifying a window."""

    def _get_available_groups(self, entry: ConfigEntry) -> list[SelectOptionDict]:
        """Get list of available groups for selection."""
        groups: list[SelectOptionDict] = [{"value": "", "label": "Keine Gruppe"}]
        try:
            if hasattr(entry, "subentries"):
                for subentry_id, subentry in entry.subentries.items():
                    if subentry.subentry_type == SUBENTRY_TYPE_GROUP:
                        groups.append(
                            {
                                "value": subentry_id,
                                "label": subentry.title or subentry_id,
                            }
                        )
        except Exception:
            pass
        return groups

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Handle the window setup step - Name, Group, Geometry, Properties."""
        entry = self._get_entry()

        if user_input is not None:
            # Get geometry section from user input
            geometry_data = user_input.get(CONF_GEOMETRY, {})

            # Build window data
            window_data = {
                "name": user_input["name"],
                CONF_GEOMETRY: {
                    CONF_WIDTH: geometry_data[CONF_WIDTH],
                    CONF_HEIGHT: geometry_data[CONF_HEIGHT],
                },
            }

            # Add optional group assignment
            group_id = user_input.get(CONF_GROUP_ID, "")
            if group_id:
                window_data[CONF_GROUP_ID] = group_id

            # Add optional geometry overrides
            if CONF_AZIMUTH in geometry_data and geometry_data[CONF_AZIMUTH] is not None:
                window_data[CONF_GEOMETRY][CONF_AZIMUTH] = geometry_data[CONF_AZIMUTH]

            if CONF_TILT in geometry_data and geometry_data[CONF_TILT] is not None:
                window_data[CONF_GEOMETRY][CONF_TILT] = geometry_data[CONF_TILT]

            # Add visible azimuth range
            if CONF_VISIBLE_AZIMUTH_START in geometry_data:
                window_data[CONF_GEOMETRY][CONF_VISIBLE_AZIMUTH_START] = geometry_data[
                    CONF_VISIBLE_AZIMUTH_START
                ]
            if CONF_VISIBLE_AZIMUTH_END in geometry_data:
                window_data[CONF_GEOMETRY][CONF_VISIBLE_AZIMUTH_END] = geometry_data[
                    CONF_VISIBLE_AZIMUTH_END
                ]

            # Add optional properties
            prop_section = user_input.get(CONF_PROPERTIES, {})
            if prop_section:
                window_data[CONF_PROPERTIES] = {}
                if CONF_G_VALUE in prop_section and prop_section[CONF_G_VALUE] is not None:
                    window_data[CONF_PROPERTIES][CONF_G_VALUE] = prop_section[CONF_G_VALUE]
                if CONF_FRAME_WIDTH in prop_section and prop_section[CONF_FRAME_WIDTH] is not None:
                    window_data[CONF_PROPERTIES][CONF_FRAME_WIDTH] = prop_section[CONF_FRAME_WIDTH]
                if (
                    CONF_WINDOW_RECESS in prop_section
                    and prop_section[CONF_WINDOW_RECESS] is not None
                ):
                    window_data[CONF_PROPERTIES][CONF_WINDOW_RECESS] = prop_section[
                        CONF_WINDOW_RECESS
                    ]
                if (
                    CONF_SHADING_DEPTH in prop_section
                    and prop_section[CONF_SHADING_DEPTH] is not None
                ):
                    window_data[CONF_PROPERTIES][CONF_SHADING_DEPTH] = prop_section[
                        CONF_SHADING_DEPTH
                    ]

            # Create the subentry - listener will reload entry to create entities
            return self.async_create_entry(
                title=window_data["name"],
                data=window_data,
                unique_id=user_input["name"],
            )  # type: ignore[return-value]

        # Get available groups
        group_options = self._get_available_groups(entry)

        # Build form with sections
        data_schema = vol.Schema(
            {
                vol.Required("name"): TextSelector(),
                vol.Optional(CONF_GROUP_ID, default=""): SelectSelector(
                    SelectSelectorConfig(options=group_options)
                ),
                vol.Required(CONF_GEOMETRY): section(
                    vol.Schema(
                        {
                            vol.Required(CONF_WIDTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=10, max=500, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Required(CONF_HEIGHT): NumberSelector(
                                NumberSelectorConfig(
                                    min=10, max=500, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_AZIMUTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=360, step=1, unit_of_measurement="°"
                                )
                            ),
                            vol.Optional(CONF_TILT, default=90): NumberSelector(
                                NumberSelectorConfig(min=0, max=90, step=1, unit_of_measurement="°")
                            ),
                            vol.Optional(CONF_VISIBLE_AZIMUTH_START, default=150): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=360, step=1, unit_of_measurement="°"
                                )
                            ),
                            vol.Optional(CONF_VISIBLE_AZIMUTH_END, default=210): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=360, step=1, unit_of_measurement="°"
                                )
                            ),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Optional(CONF_PROPERTIES, default={}): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_G_VALUE): NumberSelector(
                                NumberSelectorConfig(min=0.1, max=1.0, step=0.05)
                            ),
                            vol.Optional(CONF_FRAME_WIDTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=20, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_WINDOW_RECESS): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=100, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_SHADING_DEPTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=200, step=1, unit_of_measurement="cm"
                                )
                            ),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle reconfiguration of an existing window."""
        subentry = self._get_reconfigure_subentry()
        current_data = subentry.data
        entry = self._get_entry()

        if user_input is not None:
            # Get geometry section from user input
            geometry_data = user_input.get(CONF_GEOMETRY, {})

            # Build window data
            window_data = {
                "name": user_input["name"],
                CONF_GEOMETRY: {
                    CONF_WIDTH: geometry_data[CONF_WIDTH],
                    CONF_HEIGHT: geometry_data[CONF_HEIGHT],
                },
            }

            # Add optional group assignment
            group_id = user_input.get(CONF_GROUP_ID, "")
            if group_id:
                window_data[CONF_GROUP_ID] = group_id

            # Add optional geometry overrides
            if CONF_AZIMUTH in geometry_data and geometry_data[CONF_AZIMUTH] is not None:
                window_data[CONF_GEOMETRY][CONF_AZIMUTH] = geometry_data[CONF_AZIMUTH]

            if CONF_TILT in geometry_data and geometry_data[CONF_TILT] is not None:
                window_data[CONF_GEOMETRY][CONF_TILT] = geometry_data[CONF_TILT]

            # Add visible azimuth range
            if CONF_VISIBLE_AZIMUTH_START in geometry_data:
                window_data[CONF_GEOMETRY][CONF_VISIBLE_AZIMUTH_START] = geometry_data[
                    CONF_VISIBLE_AZIMUTH_START
                ]
            if CONF_VISIBLE_AZIMUTH_END in geometry_data:
                window_data[CONF_GEOMETRY][CONF_VISIBLE_AZIMUTH_END] = geometry_data[
                    CONF_VISIBLE_AZIMUTH_END
                ]

            # Add optional properties
            prop_section = user_input.get(CONF_PROPERTIES, {})
            if prop_section:
                window_data[CONF_PROPERTIES] = {}
                if CONF_G_VALUE in prop_section and prop_section[CONF_G_VALUE] is not None:
                    window_data[CONF_PROPERTIES][CONF_G_VALUE] = prop_section[CONF_G_VALUE]
                if CONF_FRAME_WIDTH in prop_section and prop_section[CONF_FRAME_WIDTH] is not None:
                    window_data[CONF_PROPERTIES][CONF_FRAME_WIDTH] = prop_section[CONF_FRAME_WIDTH]
                if (
                    CONF_WINDOW_RECESS in prop_section
                    and prop_section[CONF_WINDOW_RECESS] is not None
                ):
                    window_data[CONF_PROPERTIES][CONF_WINDOW_RECESS] = prop_section[
                        CONF_WINDOW_RECESS
                    ]
                if (
                    CONF_SHADING_DEPTH in prop_section
                    and prop_section[CONF_SHADING_DEPTH] is not None
                ):
                    window_data[CONF_PROPERTIES][CONF_SHADING_DEPTH] = prop_section[
                        CONF_SHADING_DEPTH
                    ]

            return self.async_update_reload_and_abort(
                entry, subentry, title=window_data["name"], data=window_data
            )

        # Get available groups
        group_options = self._get_available_groups(entry)

        current_geometry = current_data.get(CONF_GEOMETRY, {})
        current_properties = current_data.get(CONF_PROPERTIES, {})
        current_group_id = current_data.get(CONF_GROUP_ID, "")

        data_schema = vol.Schema(
            {
                vol.Required("name"): TextSelector(),
                vol.Optional(CONF_GROUP_ID): SelectSelector(
                    SelectSelectorConfig(options=group_options)
                ),
                vol.Required(CONF_GEOMETRY): section(
                    vol.Schema(
                        {
                            vol.Required(CONF_WIDTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=10, max=500, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Required(CONF_HEIGHT): NumberSelector(
                                NumberSelectorConfig(
                                    min=10, max=500, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_AZIMUTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=360, step=1, unit_of_measurement="°"
                                )
                            ),
                            vol.Optional(CONF_TILT): NumberSelector(
                                NumberSelectorConfig(min=0, max=90, step=1, unit_of_measurement="°")
                            ),
                            vol.Optional(CONF_VISIBLE_AZIMUTH_START): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=360, step=1, unit_of_measurement="°"
                                )
                            ),
                            vol.Optional(CONF_VISIBLE_AZIMUTH_END): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=360, step=1, unit_of_measurement="°"
                                )
                            ),
                        }
                    ),
                    {"collapsed": False},
                ),
                vol.Optional(CONF_PROPERTIES): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_G_VALUE): NumberSelector(
                                NumberSelectorConfig(min=0.1, max=1.0, step=0.05)
                            ),
                            vol.Optional(CONF_FRAME_WIDTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=20, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_WINDOW_RECESS): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=100, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_SHADING_DEPTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=200, step=1, unit_of_measurement="cm"
                                )
                            ),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )

        # Build suggested values from existing config
        suggested_values = {
            "name": current_data.get("name"),
            CONF_GROUP_ID: current_group_id,
            CONF_GEOMETRY: {
                CONF_WIDTH: current_geometry.get(CONF_WIDTH),
                CONF_HEIGHT: current_geometry.get(CONF_HEIGHT),
                CONF_AZIMUTH: current_geometry.get(CONF_AZIMUTH),
                CONF_TILT: current_geometry.get(CONF_TILT),
                CONF_VISIBLE_AZIMUTH_START: current_geometry.get(CONF_VISIBLE_AZIMUTH_START, 150),
                CONF_VISIBLE_AZIMUTH_END: current_geometry.get(CONF_VISIBLE_AZIMUTH_END, 210),
            },
            CONF_PROPERTIES: current_properties,
        }

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(data_schema, suggested_values),
        )


class GroupSubentryFlowHandler(ConfigSubentryFlow):
    """Handle subentry flow for adding/modifying a group."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Handle the group setup step - Name, Azimuth, Indoor Sensor, Properties."""
        if user_input is not None:
            # Build group data with name, optional azimuth and indoor sensor
            group_data = {
                "name": user_input["name"],
                CONF_SENSORS: {},
            }

            # Add optional azimuth for inheritance
            if CONF_AZIMUTH in user_input and user_input[CONF_AZIMUTH] is not None:
                group_data[CONF_AZIMUTH] = user_input[CONF_AZIMUTH]

            # Add optional indoor temperature sensor
            group_data[CONF_SENSORS][CONF_TEMP_INDOOR] = user_input.get(CONF_TEMP_INDOOR)

            # Add optional property overrides (from section)
            prop_section = user_input.get(CONF_PROPERTIES, {})
            if prop_section:
                group_data[CONF_PROPERTIES] = {}
                if CONF_G_VALUE in prop_section and prop_section[CONF_G_VALUE] is not None:
                    group_data[CONF_PROPERTIES][CONF_G_VALUE] = prop_section[CONF_G_VALUE]
                if CONF_FRAME_WIDTH in prop_section and prop_section[CONF_FRAME_WIDTH] is not None:
                    group_data[CONF_PROPERTIES][CONF_FRAME_WIDTH] = prop_section[CONF_FRAME_WIDTH]
                if (
                    CONF_WINDOW_RECESS in prop_section
                    and prop_section[CONF_WINDOW_RECESS] is not None
                ):
                    group_data[CONF_PROPERTIES][CONF_WINDOW_RECESS] = prop_section[
                        CONF_WINDOW_RECESS
                    ]
                if (
                    CONF_SHADING_DEPTH in prop_section
                    and prop_section[CONF_SHADING_DEPTH] is not None
                ):
                    group_data[CONF_PROPERTIES][CONF_SHADING_DEPTH] = prop_section[
                        CONF_SHADING_DEPTH
                    ]

            # Create the subentry - listener will reload entry to create entities
            return self.async_create_entry(
                title=group_data["name"],
                data=group_data,
                unique_id=user_input["name"],
            )  # type: ignore[return-value]

        # Form with azimuth, indoor sensor, and properties section
        data_schema = vol.Schema(
            {
                vol.Required("name"): TextSelector(),
                vol.Optional(CONF_AZIMUTH): NumberSelector(
                    NumberSelectorConfig(min=0, max=360, step=1, unit_of_measurement="°")
                ),
                vol.Optional(CONF_TEMP_INDOOR): EntitySelector(
                    EntitySelectorConfig(device_class="temperature")
                ),
                vol.Optional(CONF_PROPERTIES, default={}): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_G_VALUE): NumberSelector(
                                NumberSelectorConfig(min=0.1, max=1.0, step=0.05)
                            ),
                            vol.Optional(CONF_FRAME_WIDTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=20, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_WINDOW_RECESS): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=100, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_SHADING_DEPTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=200, step=1, unit_of_measurement="cm"
                                )
                            ),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle reconfiguration of an existing group."""
        subentry = self._get_reconfigure_subentry()
        current_data = subentry.data

        if user_input is not None:
            group_data = {
                "name": user_input["name"],
                CONF_SENSORS: {},
            }

            # Add optional azimuth for inheritance
            if CONF_AZIMUTH in user_input and user_input[CONF_AZIMUTH] is not None:
                group_data[CONF_AZIMUTH] = user_input[CONF_AZIMUTH]

            # Add optional indoor temperature sensor
            group_data[CONF_SENSORS][CONF_TEMP_INDOOR] = user_input.get(CONF_TEMP_INDOOR)

            prop_section = user_input.get(CONF_PROPERTIES, {})
            if prop_section:
                group_data[CONF_PROPERTIES] = {}
                if CONF_G_VALUE in prop_section and prop_section[CONF_G_VALUE] is not None:
                    group_data[CONF_PROPERTIES][CONF_G_VALUE] = prop_section[CONF_G_VALUE]
                if CONF_FRAME_WIDTH in prop_section and prop_section[CONF_FRAME_WIDTH] is not None:
                    group_data[CONF_PROPERTIES][CONF_FRAME_WIDTH] = prop_section[CONF_FRAME_WIDTH]
                if (
                    CONF_WINDOW_RECESS in prop_section
                    and prop_section[CONF_WINDOW_RECESS] is not None
                ):
                    group_data[CONF_PROPERTIES][CONF_WINDOW_RECESS] = prop_section[
                        CONF_WINDOW_RECESS
                    ]
                if (
                    CONF_SHADING_DEPTH in prop_section
                    and prop_section[CONF_SHADING_DEPTH] is not None
                ):
                    group_data[CONF_PROPERTIES][CONF_SHADING_DEPTH] = prop_section[
                        CONF_SHADING_DEPTH
                    ]

            return self.async_update_reload_and_abort(
                self._get_entry(), subentry, title=group_data["name"], data=group_data
            )

        current_azimuth = current_data.get(CONF_AZIMUTH)
        current_sensors = current_data.get(CONF_SENSORS, {})
        current_properties = current_data.get(CONF_PROPERTIES, {})

        data_schema = vol.Schema(
            {
                vol.Required("name"): TextSelector(),
                vol.Optional(CONF_AZIMUTH): NumberSelector(
                    NumberSelectorConfig(min=0, max=360, step=1, unit_of_measurement="°")
                ),
                vol.Optional(CONF_TEMP_INDOOR): vol.Any(
                    None, EntitySelector(EntitySelectorConfig(device_class="temperature"))
                ),
                vol.Optional(CONF_PROPERTIES): section(
                    vol.Schema(
                        {
                            vol.Optional(CONF_G_VALUE): NumberSelector(
                                NumberSelectorConfig(min=0.1, max=1.0, step=0.05)
                            ),
                            vol.Optional(CONF_FRAME_WIDTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=20, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_WINDOW_RECESS): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=100, step=1, unit_of_measurement="cm"
                                )
                            ),
                            vol.Optional(CONF_SHADING_DEPTH): NumberSelector(
                                NumberSelectorConfig(
                                    min=0, max=200, step=1, unit_of_measurement="cm"
                                )
                            ),
                        }
                    ),
                    {"collapsed": True},
                ),
            }
        )

        # Build suggested values from existing config
        suggested_values = {
            "name": current_data.get("name"),
            CONF_AZIMUTH: current_azimuth,
            CONF_TEMP_INDOOR: current_sensors.get(CONF_TEMP_INDOOR),
            CONF_PROPERTIES: current_properties,
        }

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(data_schema, suggested_values),
        )
