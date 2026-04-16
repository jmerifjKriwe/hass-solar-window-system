"""Constants for the Solar Window System integration."""

# Domain
DOMAIN = "solar_window_system"

# Configuration keys
CONF_GLOBAL = "global"
CONF_GROUPS = "groups"
CONF_WINDOWS = "windows"
CONF_SENSORS = "sensors"
CONF_THRESHOLDS = "thresholds"
CONF_PROPERTIES = "properties"
CONF_GEOMETRY = "geometry"
CONF_SEASONAL = "seasonal"

# Subentry configuration keys
CONF_GROUP_ID = "group_id"
CONF_GROUP_TYPE = "group_type"
CONF_WINDOW_IDS = "window_ids"

# Override storage key
CONF_OVERRIDES = "overrides"

# Geometry config keys
CONF_WIDTH = "width"
CONF_HEIGHT = "height"
CONF_AZIMUTH = "azimuth"
CONF_TILT = "tilt"  # Window tilt/inclination angle (0°=flat, 90°=vertical)
CONF_VISIBLE_AZIMUTH_START = "visible_azimuth_start"
CONF_VISIBLE_AZIMUTH_END = "visible_azimuth_end"

# Window property keys
CONF_G_VALUE = "g_value"
CONF_FRAME_WIDTH = "frame_width"
CONF_WINDOW_RECESS = "window_recess"
CONF_SHADING_DEPTH = "shading_depth"

# Threshold config entity keys
CONF_THRESHOLD_INDOOR = "threshold_indoor"
CONF_THRESHOLD_OUTDOOR = "threshold_outdoor"
CONF_THRESHOLD_FORECAST = "threshold_forecast"
CONF_THRESHOLD_RADIATION = "threshold_radiation"

# Scenario config entity keys
CONF_SCENARIO_INDOOR = "scenario_indoor"
CONF_SCENARIO_OUTDOOR = "scenario_outdoor"
CONF_SCENARIO_FORECAST = "scenario_forecast"

# Group types
GROUP_TYPE_ROOM = "room"
GROUP_TYPE_ORIENTATION = "orientation"

# Sensor config keys
CONF_IRRADIANCE_SENSOR = "irradiance_sensor"
CONF_IRRADIANCE_DIFFUSE_SENSOR = "irradiance_diffuse_sensor"
CONF_TEMP_OUTDOOR = "temp_outdoor"
CONF_TEMP_INDOOR = "temp_indoor"
CONF_WEATHER_WARNING = "weather_warning"
CONF_WEATHER_CONDITION = "weather_condition"

# Checkbox keys for optional sensor enablement (config flow)
CONF_USE_IRRADIANCE_DIFFUSE = "use_irradiance_diffuse"
CONF_USE_TEMP_OUTDOOR = "use_temp_outdoor"
CONF_USE_TEMP_INDOOR = "use_temp_indoor"
CONF_USE_WEATHER_WARNING = "use_weather_warning"
CONF_USE_WEATHER_CONDITION = "use_weather_condition"

# Threshold defaults
DEFAULT_OUTSIDE_TEMP = 25.0
DEFAULT_INSIDE_TEMP = 24.0
DEFAULT_FORECAST_HIGH = 28.0
DEFAULT_SOLAR_ENERGY = 300

# Property defaults
DEFAULT_G_VALUE = 0.6
DEFAULT_FRAME_WIDTH = 10
DEFAULT_WINDOW_RECESS = 0
DEFAULT_SHADING_DEPTH = 0

# Seasonal defaults
DEFAULT_SUMMER_MONTHS = [4, 5, 6, 7, 8, 9]
DEFAULT_SHADING_START = "10:00"
DEFAULT_SHADING_END = "16:00"

# Update interval
DEFAULT_UPDATE_INTERVAL = 120

# Entity types
ENERGY_TYPE_DIRECT = "direct"
ENERGY_TYPE_DIFFUSE = "diffuse"
ENERGY_TYPE_COMBINED = "combined"

# Levels
LEVEL_WINDOW = "window"
LEVEL_GROUP = "group"
LEVEL_GLOBAL = "global"

# Scenarios
SCENARIO_SEASONAL = "seasonal"
SCENARIO_FORECAST = "forecast"
SCENARIO_INSIDE_TEMP = "inside_temp"
SCENARIO_OUTSIDE_TEMP = "outside_temp"
SCENARIO_WEATHER_WARNING = "weather_warning"
SCENARIO_NONE = "none"

# Sun states
SUN_STATE_ABOVE_HORIZON = "above_horizon"
SUN_STATE_BELOW_HORIZON = "below_horizon"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "solar_window_system"

# Debug entity types
DEBUG_TYPE_CONFIG = "config"
DEBUG_TYPE_RUNTIME = "runtime"
