# /config/custom_components/solar_window_system/calculator.py

import logging
from datetime import datetime
import math
import yaml
from typing import Union

_LOGGER = logging.getLogger(__name__)


class SolarWindowCalculator:
    def __init__(self, hass, defaults_config, groups_config, windows_config):
        self.hass = hass
        self.defaults = defaults_config
        self.groups = groups_config
        self.windows = windows_config
        _LOGGER.info("Calculator initialized with %s windows.", len(self.windows))

    def get_safe_state(self, entity_id: str, default: Union[str, int, float] = 0):
        """
        Safely get the state of an entity, returning a default if it is
        unavailable, unknown, or not found.
        """
        if not entity_id:
            return default

        state = self.hass.states.get(entity_id)

        if state is None or state.state in ["unknown", "unavailable"]:
            _LOGGER.debug(
                "Entity %s not found or unavailable, returning default value.",
                entity_id,
            )
            return default

        return state.state

    # This function was missing
    def get_safe_attr(
        self, entity_id: str, attr: str, default: Union[str, int, float] = 0
    ):
        """Safely get an attribute of an entity, returning a default if unavailable."""
        if not entity_id:
            return default

        state = self.hass.states.get(entity_id)

        if state is None or state.state in ["unknown", "unavailable"]:
            _LOGGER.debug(
                "Entity %s not found or unavailable, returning default value for attribute %s.",
                entity_id,
                attr,
            )
            return default

        return state.attributes.get(attr, default)

    def get_effective_config(self, window_id):
        window_config = self.windows.get(window_id, {})
        group_type = window_config.get("group_type", "default")
        group_config = self.groups.get(group_type, {})
        effective = yaml.safe_load(yaml.safe_dump(self.defaults))
        for key in [
            "thresholds",
            "temperatures",
            "scenario_b",
            "scenario_c",
            "physical",
        ]:
            if key in group_config:
                if key not in effective:
                    effective[key] = {}
                effective[key].update(group_config[key])
        if "overrides" in window_config:
            for key, value in window_config["overrides"].items():
                if key not in effective:
                    effective[key] = {}
                if isinstance(value, dict):
                    effective[key].update(value)
                else:
                    effective[key] = value
        return effective, window_config

    def apply_global_factors(self, config, group_type, states):
        sensitivity = states.get("sensitivity", 1.0)
        config["thresholds"]["direct"] /= sensitivity
        config["thresholds"]["diffuse"] /= sensitivity

        if group_type == "children":
            factor = states.get("children_factor", 1.0)
            config["thresholds"]["direct"] *= factor
            config["thresholds"]["diffuse"] *= factor

        temp_offset = states.get("temperature_offset", 0.0)  # Changed from temp_offset
        config["temperatures"]["indoor_base"] += temp_offset
        config["temperatures"]["outdoor_base"] += temp_offset

        return config

    def calculate_window_solar_power(self, effective_config, window_config, states):
        solar_radiation = states["solar_radiation"]
        sun_azimuth = states["sun_azimuth"]
        sun_elevation = states["sun_elevation"]
        g_value, frame_width, diffuse_factor = (
            effective_config["physical"]["g_value"],
            effective_config["physical"]["frame_width"],
            effective_config["physical"]["diffuse_factor"],
        )
        glass_width, glass_height = (
            max(0, window_config["width"] - 2 * frame_width),
            max(0, window_config["height"] - 2 * frame_width),
        )
        area = glass_width * glass_height
        power_diffuse = solar_radiation * diffuse_factor * area * g_value
        power_direct = 0
        is_visible = False
        if (
            sun_elevation >= window_config["elevation_range"][0]
            and sun_elevation <= window_config["elevation_range"][1]
        ):
            az_diff = ((sun_azimuth - window_config["azimuth"] + 180) % 360) - 180
            az_min, az_max = window_config["azimuth_range"]
            if az_min <= az_diff <= az_max:
                is_visible = True
                sun_el_rad, sun_az_rad, win_az_rad, tilt_rad = (
                    math.radians(sun_elevation),
                    math.radians(sun_azimuth),
                    math.radians(window_config["azimuth"]),
                    math.radians(effective_config["physical"]["tilt"]),
                )
                cos_incidence = math.sin(sun_el_rad) * math.cos(tilt_rad) + math.cos(
                    sun_el_rad
                ) * math.sin(tilt_rad) * math.cos(sun_az_rad - win_az_rad)
                if cos_incidence > 0 and sun_el_rad > 0:
                    power_direct = (
                        (
                            solar_radiation
                            * (1 - diffuse_factor)
                            * cos_incidence
                            / math.sin(sun_el_rad)
                        )
                        * area
                        * g_value
                    )
        return {
            "power_total": power_direct + power_diffuse,
            "power_direct": power_direct,
            "power_diffuse": power_diffuse,
            "is_visible": is_visible,
            "area_m2": area,
        }

    def should_shade_window(self, window_data, effective_config, window_config, states):
        if states["weather_warning"]:
            return True, "Weather warning active"
        try:
            indoor_temp_str = self.get_safe_state(
                window_config["room_temp_entity"], "0"
            )
            indoor_temp = float(indoor_temp_str)
            outdoor_temp = states["outdoor_temp"]
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Could not parse temperature for window %s",
                window_config.get("name", "Unknown"),
            )
            return False, "Invalid temperature data"

        threshold_direct = effective_config["thresholds"]["direct"]

        if (
            window_data["power_total"] > threshold_direct
            and indoor_temp >= effective_config["temperatures"]["indoor_base"]
            and outdoor_temp >= effective_config["temperatures"]["outdoor_base"]
        ):
            return (
                True,
                f"Strong sun ({window_data['power_total']:.0f}W > {threshold_direct:.0f}W)",
            )

        return False, "No shading required"

    def calculate_all_windows(self, current_options: dict):
        """
        Main calculation function.
        """
        conf = current_options  # Use the passed-in options directly
        solar_rad_entity = conf.get("solar_radiation_sensor") or ""
        outdoor_temp_entity = conf.get("outdoor_temperature_sensor") or ""
        weather_warning_entity = conf.get("weather_warning_sensor") or ""

        external_states = {
            "sensitivity": float(conf.get("global_sensitivity", 1.0)),
            "children_factor": float(conf.get("children_factor", 0.8)),
            "temperature_offset": float(conf.get("temperature_offset", 0.0)),
            "scenario_b_enabled": conf.get("scenario_b_enabled", True),
            "scenario_c_enabled": conf.get("scenario_c_enabled", True),
            "debug_mode": conf.get("debug_mode", False),
            "maintenance_mode": conf.get("maintenance_mode", False),
            "solar_radiation": float(self.get_safe_state(solar_rad_entity, 0)),
            "sun_azimuth": float(self.get_safe_attr("sun.sun", "azimuth", 0)),
            "sun_elevation": float(self.get_safe_attr("sun.sun", "elevation", 0)),
            "outdoor_temp": float(self.get_safe_state(outdoor_temp_entity, 0)),
            "weather_warning": self.get_safe_state(weather_warning_entity, "off")
            == "on",
        }

        results = {}
        total_power, shading_count = 0, 0

        # Process each window
        for window_id, window_config in self.windows.items():
            try:
                # Get effective configuration for this window
                effective_config, _ = self.get_effective_config(window_id)

                # Apply global factors
                group_type = window_config.get("group_type", "default")
                effective_config = self.apply_global_factors(
                    effective_config, group_type, external_states
                )

                # Calculate solar power for this window
                solar_data = self.calculate_window_solar_power(
                    effective_config, window_config, external_states
                )

                # Determine if shading is required
                shade_required, shade_reason = self.should_shade_window(
                    solar_data, effective_config, window_config, external_states
                )

                # Store results for this window
                results[window_id] = {
                    "name": window_config.get("name", window_id),
                    "power_total": solar_data["power_total"],
                    "power_direct": solar_data["power_direct"],
                    "power_diffuse": solar_data["power_diffuse"],
                    "area_m2": solar_data["area_m2"],
                    "is_visible": solar_data["is_visible"],
                    "shade_required": shade_required,
                    "shade_reason": shade_reason,
                    "effective_threshold": effective_config["thresholds"]["direct"],
                }

                # Update totals
                total_power += solar_data["power_total"]
                if shade_required:
                    shading_count += 1

            except Exception as e:
                _LOGGER.error(f"Error calculating window {window_id}: {e}")
                # Add a minimal result to prevent crashes
                results[window_id] = {
                    "name": window_config.get("name", window_id),
                    "power_total": 0,
                    "power_direct": 0,
                    "power_diffuse": 0,
                    "area_m2": 0,
                    "is_visible": False,
                    "shade_required": False,
                    "shade_reason": f"Calculation error: {e}",
                    "effective_threshold": 0,
                }

        # Add summary
        results["summary"] = {
            "total_power": total_power,
            "window_count": len(self.windows),
            "shading_count": shading_count,
            "calculation_time": datetime.now().isoformat(),
        }

        _LOGGER.debug(
            f"Calculated data for {len(self.windows)} windows, total power: {total_power:.1f}W"
        )
        return results
