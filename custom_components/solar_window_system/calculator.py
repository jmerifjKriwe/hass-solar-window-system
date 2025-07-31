# /config/custom_components/solar_window_system/calculator.py

import logging
from datetime import datetime
import math

_LOGGER = logging.getLogger(__name__)


class SolarWindowCalculator:
    def __init__(self, hass, global_config):
        self.hass = hass
        self.global_config = global_config
        _LOGGER.info("Calculator initialized with global configuration.")

    def get_safe_state(self, entity_id: str, default: str | int | float = 0):
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

    def get_safe_attr(
        self, entity_id: str, attr: str, default: str | int | float = 0
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

    def get_effective_config(self, window_config: dict):
        """Get effective configuration by merging window config with global config and applying overrides."""
        effective_config = self.global_config.copy()

        # Apply window-specific overrides
        for key, value in window_config.items():
            if key in ["g_value", "frame_width", "tilt", "diffuse_factor"]:
                effective_config["physical"][key] = value
            elif key in ["threshold_direct", "threshold_diffuse"]:
                effective_config["thresholds"][key] = value
            elif key in ["indoor_base", "outdoor_base"]:
                effective_config["temperatures"][key] = value
            elif key in ["scenario_b_temp_indoor_threshold", "scenario_b_temp_outdoor_threshold"]:
                effective_config["scenario_b"][key] = value
            elif key in ["scenario_c_temp_forecast_threshold", "scenario_c_temp_indoor_threshold", "scenario_c_temp_outdoor_threshold", "scenario_c_start_hour"]:
                effective_config["scenario_c"][key] = value
            elif key == "min_sun_elevation":
                effective_config["calculation"][key] = value

        # Calculate and add azimuth and elevation ranges (these should probably be part of window_config directly)
        window_config["azimuth_range"] = window_config.get("azimuth_range", (-90, 90))
        window_config["elevation_range"] = window_config.get("elevation_range", (
            effective_config.get("calculation", {}).get("min_sun_elevation", 10),
            90,
        ))

        return effective_config, window_config

    def apply_global_factors(self, config, states):
        sensitivity = states.get("sensitivity", 1.0)
        if sensitivity > 0:
            config["thresholds"]["direct"] /= sensitivity
            config["thresholds"]["diffuse"] /= sensitivity

        temp_offset = states.get("temperature_offset", 0.0)
        config["temperatures"]["indoor_base"] += temp_offset
        config["temperatures"]["outdoor_base"] += temp_offset

        return config

    def calculate_window_solar_power(self, effective_config, window_config, states):
        solar_radiation = states["solar_radiation"]
        sun_azimuth = states["sun_azimuth"]
        sun_elevation = states["sun_elevation"]
        g_value, frame_width, diffuse_factor = (
            effective_config["physical"]["g_value"],
            effective_config["physical"]["g_value"],
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

        _LOGGER.debug(
            "[CALC] ---- Solar Power Calculation for %s ----", window_config.get("name")
        )
        _LOGGER.debug(
            "[CALC] Sun Elevation: %s, Sun Azimuth: %s", sun_elevation, sun_azimuth
        )
        _LOGGER.debug(
            "[CALC] Window Azimuth: %s, Elevation Range: %s, Azimuth Range: %s",
            window_config["azimuth"],
            window_config["elevation_range"],
            window_config["azimuth_range"],
        )

        if (
            sun_elevation >= window_config["elevation_range"][0]
            and sun_elevation <= window_config["elevation_range"][1]
        ):
            az_diff = ((sun_azimuth - window_config["azimuth"] + 180) % 360) - 180
            az_min, az_max = window_config["azimuth_range"]
            _LOGGER.debug(
                "[CALC] Azimuth Difference: %s (Min: %s, Max: %s)",
                az_diff,
                az_min,
                az_max,
            )
            if az_min <= az_diff <= az_max:
                is_visible = True
                _LOGGER.debug("[CALC] Sun is VISIBLE to the window.")
                sun_el_rad, sun_az_rad, win_az_rad, tilt_rad = (
                    math.radians(sun_elevation),
                    math.radians(sun_azimuth),
                    math.radians(window_config["azimuth"]),
                    math.radians(effective_config["physical"]["tilt"]),
                )
                cos_incidence = math.sin(sun_el_rad) * math.cos(tilt_rad) + math.cos(
                    math.radians(sun_el_rad)
                ) * math.sin(tilt_rad) * math.cos(sun_az_rad - win_az_rad)
                _LOGGER.debug("[CALC] Cosine of Incidence Angle: %s", cos_incidence)
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
        else:
            _LOGGER.debug("[CALC] Sun is OUTSIDE elevation range.")

        _LOGGER.debug(
            "[CALC] Power Direct: %.2f W, Power Diffuse: %.2f W",
            power_direct,
            power_diffuse,
        )
        _LOGGER.debug("[CALC] Total Power: %.2f W", power_direct + power_diffuse)
        return {
            "power_total": power_direct + power_diffuse,
            "power_direct": power_direct,
            "power_diffuse": power_diffuse,
            "is_visible": is_visible,
            "area_m2": area,
        }

    def should_shade_window(self, window_data, effective_config, window_config, states):
        """
        Decides if shading is required based on various scenarios (A, B, C).
        """
        _LOGGER.debug(
            "[SHADE] ---- Shading Logic for %s ----", window_config.get("name")
        )

        if states["maintenance_mode"]:
            _LOGGER.debug("[SHADE] Result: OFF (Maintenance mode active)")
            return False, "Maintenance mode active"

        if states["weather_warning"]:
            _LOGGER.debug("[SHADE] Result: ON (Weather warning active)")
            return True, "Weather warning active"

        try:
            indoor_temp_str = self.get_safe_state(
                window_config["room_temp_entity"], "0"
            )
            indoor_temp = float(indoor_temp_str)
            outdoor_temp = states["outdoor_temp"]
            _LOGGER.debug(
                "[SHADE] Temps - Indoor: %.1f°C, Outdoor: %.1f°C",
                indoor_temp,
                outdoor_temp,
            )
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Could not parse temperature for window %s",
                window_config.get("name", "Unknown"),
            )
            return False, "Invalid temperature data"

        # --- Scenario A: Strong direct sun ---
        threshold_direct = effective_config["thresholds"]["direct"]
        _LOGGER.debug(
            "[SHADE] Scenario A Check: Power (%.1fW) > Threshold (%.1fW)? AND Indoor (%.1f°C) >= Base (%.1f°C)? AND Outdoor (%.1f°C) >= Base (%.1f°C)?",
            window_data["power_total"],
            threshold_direct,
            indoor_temp,
            effective_config["temperatures"]["indoor_base"],
            outdoor_temp,
            effective_config["temperatures"]["outdoor_base"],
        )
        if (
            window_data["power_total"] > threshold_direct
            and indoor_temp >= effective_config["temperatures"]["indoor_base"]
            and outdoor_temp >= effective_config["temperatures"]["outdoor_base"]
        ):
            _LOGGER.debug("[SHADE] Result: ON (Scenario A triggered)")
            return (
                True,
                f"Strong sun ({window_data['power_total']:.0f}W > {threshold_direct:.0f}W)",
            )

        # --- Scenario B: Diffuse heat ---
        scenario_b_config = effective_config.get("scenario_b", {})
        if states["scenario_b_enabled"] and scenario_b_config.get("enabled", True):
            threshold_diffuse = effective_config["thresholds"]["diffuse"]
            temp_indoor_b = effective_config["temperatures"][
                "indoor_base"
            ] + scenario_b_config.get("temp_indoor_offset", 0.5)
            temp_outdoor_b = effective_config["temperatures"][
                "outdoor_base"
            ] + scenario_b_config.get("temp_outdoor_offset", 6.0)

            _LOGGER.debug(
                "[SHADE] Scenario B Check: Power (%.1fW) > Threshold (%.1fW)? AND Indoor (%.1f°C) > Offset (%.1f°C)? AND Outdoor (%.1f°C) > Offset (%.1f°C)?",
                window_data["power_total"],
                threshold_diffuse,
                indoor_temp,
                temp_indoor_b,
                outdoor_temp,
                temp_outdoor_b,
            )

            if (
                window_data["power_total"] > threshold_diffuse
                and indoor_temp > temp_indoor_b
                and outdoor_temp > temp_outdoor_b
            ):
                _LOGGER.debug("[SHADE] Result: ON (Scenario B triggered)")
                return (
                    True,
                    f"Diffuse heat ({window_data['power_total']:.0f}W, Indoor: {indoor_temp:.1f}°C)",
                )

        # --- Scenario C: Heatwave forecast ---
        scenario_c_config = effective_config.get("scenario_c", {})
        if states["scenario_c_enabled"] and scenario_c_config.get("enabled", True):
            try:
                forecast_temp = states["forecast_temp"]
                if forecast_temp > 0:
                    current_hour = datetime.now().hour
                    temp_forecast_threshold = scenario_c_config.get(
                        "temp_forecast_threshold", 28.5
                    )
                    start_hour = scenario_c_config.get("start_hour", 9)

                    _LOGGER.debug(
                        "[SHADE] Scenario C Check: Forecast (%.1f°C) > Threshold (%.1f°C)? AND Indoor (%.1f°C) >= Base (%.1f°C)? AND Hour (%d) >= Start (%d)?",
                        forecast_temp,
                        temp_forecast_threshold,
                        indoor_temp,
                        effective_config["temperatures"]["indoor_base"],
                        current_hour,
                        start_hour,
                    )

                    if (
                        forecast_temp > temp_forecast_threshold
                        and indoor_temp
                        >= effective_config["temperatures"]["indoor_base"]
                        and current_hour >= start_hour
                    ):
                        _LOGGER.debug("[SHADE] Result: ON (Scenario C triggered)")
                        return (
                            True,
                            f"Heatwave forecast ({forecast_temp:.1f}°C expected)",
                        )
            except (ValueError, TypeError):
                _LOGGER.warning("Could not read forecast temperature for Scenario C")

        _LOGGER.debug("[SHADE] Result: OFF (No shading required)")
        return False, "No shading required"

    def calculate_all_windows(self, window_configs: dict, global_options: dict):
        """
        Main calculation function. Returns empty summary if no windows are configured.
        """
        if not window_configs:
            _LOGGER.info("No windows configured. Calculation returns empty summary.")
            return {
                "summary": {
                    "total_power": 0,
                    "window_count": 0,
                    "shading_count": 0,
                    "calculation_time": None,
                }
            }

        solar_rad_entity = global_options.get("solar_radiation_sensor") or ""
        outdoor_temp_entity = global_options.get("outdoor_temperature_sensor") or ""
        weather_warning_entity = global_options.get("weather_warning_sensor") or ""
        forecast_temp_entity = global_options.get("forecast_temperature_sensor") or ""

        external_states = {
            "sensitivity": float(global_options.get("global_sensitivity", 1.0)),
            "children_factor": float(global_options.get("children_factor", 0.8)),
            "temperature_offset": float(global_options.get("temperature_offset", 0.0)),
            "scenario_b_enabled": global_options.get("scenario_b_enabled", True),
            "scenario_c_enabled": global_options.get("scenario_c_enabled", True),
            "debug_mode": global_options.get("debug_mode", False),
            "maintenance_mode": global_options.get("maintenance_mode", False),
            "solar_radiation": float(self.get_safe_state(solar_rad_entity, 0)),
            "sun_azimuth": float(self.get_safe_attr("sun.sun", "azimuth", 0)),
            "sun_elevation": float(self.get_safe_attr("sun.sun", "elevation", 0)),
            "outdoor_temp": float(self.get_safe_state(outdoor_temp_entity, 0)),
            "forecast_temp": float(self.get_safe_state(forecast_temp_entity, 0)),
            "weather_warning": self.get_safe_state(weather_warning_entity, "off")
            == "on",
        }

        _LOGGER.debug("---- Starting Full Calculation Cycle ----")
        _LOGGER.debug("Global Options in calculate_all_windows: %s", global_options)
        _LOGGER.debug("External States: %s", external_states)

        results = {}
        total_power, shading_count = 0, 0

        for window_id, window_config in window_configs.items():
            try:
                effective_config, _ = self.get_effective_config(window_config)
                effective_config = self.apply_global_factors(
                    effective_config, external_states
                )
                solar_data = self.calculate_window_solar_power(
                    effective_config, window_config, external_states
                )
                shade_required, shade_reason = self.should_shade_window(
                    solar_data, effective_config, window_config, external_states
                )
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
                total_power += solar_data["power_total"]
                if shade_required:
                    shading_count += 1
            except Exception as e:
                _LOGGER.error(
                    f"Error calculating window {window_id}: {e}", exc_info=True
                )
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
        results["summary"] = {
            "total_power": total_power,
            "window_count": len(window_configs),
            "shading_count": shading_count,
            "calculation_time": datetime.now().isoformat(),
        }
        _LOGGER.debug("---- Full Calculation Cycle Finished ----")
        return results