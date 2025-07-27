"""Constants for solar_window_system."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "solar_window_system"
PLATFORMS: list[str] = ["sensor", "binary_sensor", "number", "select", "switch"]
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
