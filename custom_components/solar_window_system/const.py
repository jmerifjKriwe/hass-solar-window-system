"""Constants for solar_window_system."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "solar_window_system"
PLATFORMS: list[str] = ["sensor", "binary_sensor", "number", "select", "switch"]
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

# New Constants for Config Flow
CONF_ENTRY_TYPE = "entry_type"
CONF_WINDOW_NAME = "window_name"
CONF_AZIMUTH = "azimuth"
CONF_AZIMUTH_RANGE = "azimuth_range"
CONF_ELEVATION_RANGE = "elevation_range"
CONF_WIDTH = "width"
CONF_HEIGHT = "height"
CONF_SHADOW_DEPTH = "shadow_depth"
CONF_SHADOW_OFFSET = "shadow_offset"
CONF_ROOM_TEMP_ENTITY = "room_temp_entity"
CONF_GROUP_NAME = "group_name"