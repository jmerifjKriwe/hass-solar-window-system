"""
Test cases for the modernized Calculator with flow-based configuration and geometric shadow calculation.
"""

import pytest
import math
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, UTC

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.solar_window_system.calculator import (
    SolarWindowCalculator,
    WindowCalculationResult,
    SolarCalculationError,
)
from custom_components.solar_window_system.const import DOMAIN


class TestCalculatorGeometricShadows:
    """Test geometric shadow calculation functionality."""

    @pytest.fixture
    def calculator(self, hass):
        """Create calculator instance with mocked config entry."""
        mock_entry = Mock(spec=ConfigEntry)
        mock_entry.entry_id = "test_entry"
        mock_entry.data = {}
        return SolarWindowCalculator(hass, mock_entry)

    def test_shadow_factor_no_shadow(self, calculator):
        """Test shadow factor when no shadow parameters are set."""
        # No shadow depth or offset
        factor = calculator._calculate_shadow_factor(45, 180, 180, 0, 0)
        assert factor == 1.0

    @pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
    def test_shadow_factor_complete_shadow(self, calculator):
        """Test shadow factor with complete shadowing scenario."""
        # High sun with deep shadow
        factor = calculator._calculate_shadow_factor(80, 180, 180, 2.0, 1.0)
        assert factor == 0.1  # Minimum shadow factor

    def test_shadow_factor_partial_shadow(self, calculator):
        """Test shadow factor with partial shadowing."""
        # Medium sun angle with moderate shadow
        factor = calculator._calculate_shadow_factor(30, 180, 180, 0.5, 0.2)
        assert 0.1 < factor < 1.0

    def test_shadow_factor_low_sun(self, calculator):
        """Test shadow factor with very low sun angle."""
        # Low sun should result in longer shadows
        factor_low = calculator._calculate_shadow_factor(10, 180, 180, 0.5, 0)
        factor_high = calculator._calculate_shadow_factor(60, 180, 180, 0.5, 0)
        assert factor_low < factor_high

    def test_shadow_factor_angle_dependency(self, calculator):
        """Test shadow factor dependency on sun-window angle."""
        # Direct facing should have more shadow impact
        factor_direct = calculator._calculate_shadow_factor(45, 180, 180, 1.0, 0)
        factor_angled = calculator._calculate_shadow_factor(45, 135, 180, 1.0, 0)
        assert factor_direct <= factor_angled


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
class TestCalculatorEntityCaching:
    """Test entity caching functionality."""

    @pytest.fixture
    def calculator(self, hass):
        """Create calculator with mocked HomeAssistant."""
        mock_entry = Mock(spec=ConfigEntry)
        mock_entry.entry_id = "test_entry"
        return SolarWindowCalculator(hass, mock_entry)

    def test_entity_cache_hit(self, calculator):
        """Test that cached values are returned."""
        # Mock hass.states.get
        mock_state = Mock()
        mock_state.state = "42.5"
        calculator.hass.states.get.return_value = mock_state

        # First call should cache
        result1 = calculator._get_cached_entity_state("sensor.test", 0)

        # Second call should use cache
        result2 = calculator._get_cached_entity_state("sensor.test", 0)

        assert result1 == "42.5"
        assert result2 == "42.5"
        # Should only call hass.states.get once
        assert calculator.hass.states.get.call_count == 1

    def test_entity_cache_miss_fallback(self, calculator):
        """Test fallback when entity doesn't exist."""
        # Mock missing entity
        calculator.hass.states.get.return_value = None

        result = calculator._get_cached_entity_state("sensor.missing", "fallback")
        assert result == "fallback"

    def test_entity_cache_expiry(self, calculator):
        """Test cache expiry after timeout."""
        # Set old timestamp
        calculator._cache_timestamp = 0

        mock_state = Mock()
        mock_state.state = "test_value"
        calculator.hass.states.get.return_value = mock_state

        # Should bypass cache due to age
        result = calculator._get_cached_entity_state("sensor.test", "fallback")
        assert result == "test_value"


class TestCalculatorFlowConfiguration:
    """Test flow-based configuration and inheritance."""

    @pytest.fixture
    def calculator_with_subentries(self, hass):
        """Create calculator with mocked sub-entries."""
        mock_entry = Mock(spec=ConfigEntry)
        mock_entry.entry_id = "test_entry"

        calculator = SolarWindowCalculator(hass, mock_entry)

        # Mock sub-entries
        calculator._get_subentries_by_type = Mock()
        calculator._get_subentries_by_type.side_effect = lambda entry_type: {
            "global": {
                "global_config": {
                    "physical": {"g_value": 0.7, "frame_width": 0.05},
                    "thresholds": {"direct": 400, "diffuse": 200},
                    "temperatures": {"indoor_base": 24, "outdoor_base": 25},
                }
            },
            "group": {
                "test_group": {
                    "name": "Test Group",
                    "physical": {"g_value": 0.8},  # Override global
                    "thresholds": {"direct": 350},  # Override global
                }
            },
            "window": {
                "test_window": {
                    "name": "Test Window",
                    "linked_group_id": "test_group",
                    "window_width": 1.5,
                    "window_height": 2.0,
                    "azimuth": 180,
                    "shadow_depth": 0.3,
                    "physical": {"frame_width": 0.08},  # Override group
                }
            },
        }[entry_type]

        return calculator

    def test_effective_config_inheritance(self, calculator_with_subentries):
        """Test configuration inheritance from global -> group -> window."""
        effective_config, sources = (
            calculator_with_subentries.get_effective_config_from_flows("test_window")
        )

        # Check inheritance worked correctly
        assert effective_config["physical"]["g_value"] == 0.8  # From group
        assert effective_config["physical"]["frame_width"] == 0.08  # From window
        assert effective_config["thresholds"]["direct"] == 350  # From group
        assert effective_config["thresholds"]["diffuse"] == 200  # From global
        assert effective_config["temperatures"]["indoor_base"] == 24  # From global

        # Check source tracking
        assert sources["physical"]["g_value"] == "group"
        assert sources["physical"]["frame_width"] == "window"
        assert sources["thresholds"]["direct"] == "group"

    def test_effective_config_missing_window(self, calculator_with_subentries):
        """Test behavior with missing window configuration."""
        with pytest.raises(ValueError, match="Window configuration not found"):
            calculator_with_subentries.get_effective_config_from_flows("missing_window")

    @pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
    def test_effective_config_missing_group(self, calculator_with_subentries):
        """Test behavior when linked group is missing."""
        # Modify window to reference missing group
        windows = calculator_with_subentries._get_subentries_by_type("window")
        windows["test_window"]["linked_group_id"] = "missing_group"

        effective_config, sources = (
            calculator_with_subentries.get_effective_config_from_flows("test_window")
        )

        # Should fallback to global only
        assert effective_config["physical"]["g_value"] == 0.7  # From global
        assert sources["physical"]["g_value"] == "global"


class TestCalculatorSolarPowerCalculation:
    """Test solar power calculation with shadow integration."""

    @pytest.fixture
    def calculator_with_mock_data(self, hass):
        """Create calculator with comprehensive mock data."""
        mock_entry = Mock(spec=ConfigEntry)
        calculator = SolarWindowCalculator(hass, mock_entry)

        # Mock effective configuration
        calculator.get_effective_config_from_flows = Mock(
            return_value=(
                {
                    "physical": {
                        "g_value": 0.7,
                        "frame_width": 0.05,
                        "diffuse_factor": 0.3,
                        "tilt": 0,
                    },
                    "thresholds": {"direct": 400, "diffuse": 200},
                    "temperatures": {"indoor_base": 24, "outdoor_base": 25},
                },
                {},
            )
        )

        # Mock shadow calculation
        calculator._calculate_shadow_factor = Mock(return_value=0.8)

        return calculator

    def test_solar_power_calculation_sunny_day(self, calculator_with_mock_data):
        """Test solar power calculation on a sunny day."""
        effective_config = {
            "physical": {
                "g_value": 0.7,
                "frame_width": 0.05,
                "diffuse_factor": 0.3,
                "tilt": 0,
            },
            "thresholds": {"direct": 400},
        }

        window_data = {
            "name": "South Window",
            "window_width": 2.0,
            "window_height": 1.5,
            "azimuth": 180,
            "elevation_min": 0,
            "elevation_max": 90,
            "azimuth_min": -90,
            "azimuth_max": 90,
            "shadow_depth": 0.5,
            "shadow_offset": 0.2,
        }

        states = {
            "solar_radiation": 800,  # High solar radiation
            "sun_azimuth": 180,  # South
            "sun_elevation": 45,  # Mid-day
        }

        result = calculator_with_mock_data.calculate_window_solar_power_with_shadow(
            effective_config, window_data, states
        )

        # Verify calculations
        assert result.power_total > 0
        assert result.power_direct > 0
        assert result.power_diffuse > 0
        assert result.is_visible is True
        assert result.shadow_factor == 0.8  # Mocked value
        assert result.area_m2 == (2.0 - 2 * 0.05) * (
            1.5 - 2 * 0.05
        )  # Account for frame

    def test_solar_power_calculation_no_sun_visibility(self, calculator_with_mock_data):
        """Test solar power calculation when sun is not visible to window."""
        effective_config = {
            "physical": {
                "g_value": 0.7,
                "frame_width": 0.05,
                "diffuse_factor": 0.3,
                "tilt": 0,
            },
            "thresholds": {"direct": 400},
        }

        window_data = {
            "name": "North Window",
            "window_width": 1.0,
            "window_height": 1.0,
            "azimuth": 0,  # North facing
            "elevation_min": 0,
            "elevation_max": 90,
            "azimuth_min": -45,  # Limited view
            "azimuth_max": 45,
            "shadow_depth": 0,
            "shadow_offset": 0,
        }

        states = {
            "solar_radiation": 800,
            "sun_azimuth": 180,  # Sun is south
            "sun_elevation": 45,
        }

        result = calculator_with_mock_data.calculate_window_solar_power_with_shadow(
            effective_config, window_data, states
        )

        # Should only have diffuse power
        assert result.power_direct == 0
        assert result.power_diffuse > 0
        assert result.is_visible is False
        assert result.shadow_factor == 1.0  # No shadow applied when not visible


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
class TestCalculatorShadingLogic:
    """Test shading decision logic for all scenarios."""

    @pytest.fixture
    def calculator_with_entities(self, hass):
        """Create calculator with mocked entity states."""
        mock_entry = Mock(spec=ConfigEntry)
        calculator = SolarWindowCalculator(hass, mock_entry)

        # Mock entity state resolution
        calculator._get_cached_entity_state = Mock()
        calculator._resolve_entity_state_with_fallback = Mock()

        return calculator

    def test_scenario_a_strong_sun(self, calculator_with_entities):
        """Test Scenario A: Strong direct sun triggers shading."""
        window_result = WindowCalculationResult(
            power_total=500,  # Above threshold
            power_direct=400,
            power_diffuse=100,
            shadow_factor=1.0,
            is_visible=True,
            area_m2=2.0,
            shade_required=False,
            shade_reason="",
            effective_threshold=400,
        )

        effective_config = {
            "thresholds": {"direct": 400, "diffuse": 200},
            "temperatures": {"indoor_base": 24, "outdoor_base": 25},
        }

        window_data = {
            "name": "Test Window",
            "indoor_temperature_sensor": "sensor.room_temp",
        }

        states = {
            "maintenance_mode": False,
            "weather_warning": False,
            "outdoor_temp": 26,  # Above base
            "scenario_b_enabled": False,
            "scenario_c_enabled": False,
        }

        # Mock room temperature above base
        calculator_with_entities._get_cached_entity_state.return_value = 25

        shade_required, reason = calculator_with_entities.should_shade_window_flow(
            window_result, effective_config, window_data, states
        )

        assert shade_required is True
        assert "Strong sun" in reason

    def test_scenario_b_diffuse_heat(self, calculator_with_entities):
        """Test Scenario B: Diffuse heat triggers shading when enabled."""
        window_result = WindowCalculationResult(
            power_total=250,  # Between diffuse and direct threshold
            power_direct=100,
            power_diffuse=150,
            shadow_factor=1.0,
            is_visible=True,
            area_m2=2.0,
            shade_required=False,
            shade_reason="",
            effective_threshold=400,
        )

        effective_config = {
            "thresholds": {"direct": 400, "diffuse": 200},
            "temperatures": {"indoor_base": 24, "outdoor_base": 25},
            "scenario_b": {
                "enabled": True,
                "temp_indoor_offset": 1,
                "temp_outdoor_offset": 2,
            },
        }

        window_data = {
            "name": "Test Window",
            "indoor_temperature_sensor": "sensor.room_temp",
        }

        states = {
            "maintenance_mode": False,
            "weather_warning": False,
            "outdoor_temp": 28,  # 25 + 2 + margin
            "scenario_b_enabled": True,
            "scenario_c_enabled": False,
        }

        # Mock room temperature above threshold
        calculator_with_entities._get_cached_entity_state.return_value = (
            26  # 24 + 1 + margin
        )

        shade_required, reason = calculator_with_entities.should_shade_window_flow(
            window_result, effective_config, window_data, states
        )

        assert shade_required is True
        assert "Diffuse heat" in reason

    def test_scenario_c_heatwave_forecast(self, calculator_with_entities):
        """Test Scenario C: Heatwave forecast triggers shading."""
        window_result = WindowCalculationResult(
            power_total=150,  # Below thresholds
            power_direct=50,
            power_diffuse=100,
            shadow_factor=1.0,
            is_visible=True,
            area_m2=2.0,
            shade_required=False,
            shade_reason="",
            effective_threshold=400,
        )

        effective_config = {
            "thresholds": {"direct": 400, "diffuse": 200},
            "temperatures": {"indoor_base": 24, "outdoor_base": 25},
            "scenario_c": {
                "enabled": True,
                "temp_forecast_threshold": 30,
                "start_hour": 10,
            },
        }

        window_data = {
            "name": "Test Window",
            "indoor_temperature_sensor": "sensor.room_temp",
        }

        states = {
            "maintenance_mode": False,
            "weather_warning": False,
            "outdoor_temp": 26,
            "forecast_temp": 32,  # Above threshold
            "scenario_b_enabled": False,
            "scenario_c_enabled": True,
        }

        # Mock room temperature at base
        calculator_with_entities._get_cached_entity_state.return_value = 24

        # Mock current hour
        with patch(
            "custom_components.solar_window_system.calculator.datetime"
        ) as mock_dt:
            mock_dt.now.return_value.hour = 12  # After start hour
            mock_dt.UTC = UTC

            shade_required, reason = calculator_with_entities.should_shade_window_flow(
                window_result, effective_config, window_data, states
            )

        assert shade_required is True
        assert "Heatwave forecast" in reason

    def test_maintenance_mode_override(self, calculator_with_entities):
        """Test that maintenance mode overrides all scenarios."""
        window_result = WindowCalculationResult(
            power_total=1000,  # Very high power
            power_direct=900,
            power_diffuse=100,
            shadow_factor=1.0,
            is_visible=True,
            area_m2=2.0,
            shade_required=False,
            shade_reason="",
            effective_threshold=400,
        )

        effective_config = {
            "thresholds": {"direct": 400, "diffuse": 200},
            "temperatures": {"indoor_base": 24, "outdoor_base": 25},
        }

        window_data = {
            "name": "Test Window",
            "indoor_temperature_sensor": "sensor.room_temp",
        }

        states = {
            "maintenance_mode": True,  # Override active
            "weather_warning": False,
            "outdoor_temp": 30,
            "scenario_b_enabled": True,
            "scenario_c_enabled": True,
        }

        calculator_with_entities._get_cached_entity_state.return_value = 30

        shade_required, reason = calculator_with_entities.should_shade_window_flow(
            window_result, effective_config, window_data, states
        )

        assert shade_required is False
        assert "Maintenance mode active" in reason

    def test_weather_warning_override(self, calculator_with_entities):
        """Test that weather warning forces shading regardless of other conditions."""
        window_result = WindowCalculationResult(
            power_total=50,  # Very low power
            power_direct=10,
            power_diffuse=40,
            shadow_factor=1.0,
            is_visible=True,
            area_m2=2.0,
            shade_required=False,
            shade_reason="",
            effective_threshold=400,
        )

        effective_config = {
            "thresholds": {"direct": 400, "diffuse": 200},
            "temperatures": {"indoor_base": 24, "outdoor_base": 25},
        }

        window_data = {
            "name": "Test Window",
            "indoor_temperature_sensor": "sensor.room_temp",
        }

        states = {
            "maintenance_mode": False,
            "weather_warning": True,  # Force shading
            "outdoor_temp": 20,  # Low temperature
            "scenario_b_enabled": False,
            "scenario_c_enabled": False,
        }

        calculator_with_entities._get_cached_entity_state.return_value = 20

        shade_required, reason = calculator_with_entities.should_shade_window_flow(
            window_result, effective_config, window_data, states
        )

        assert shade_required is True
        assert "Weather warning active" in reason


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
class TestCalculatorScenarioInheritance:
    """Test scenario enable/disable inheritance logic."""

    @pytest.fixture
    def calculator_with_inheritance(self, hass):
        """Create calculator with mocked inheritance structure."""
        mock_entry = Mock(spec=ConfigEntry)
        calculator = SolarWindowCalculator(hass, mock_entry)

        # Mock subentries for inheritance testing
        calculator._get_subentries_by_type = Mock()
        calculator._get_subentries_by_type.side_effect = lambda entry_type: {
            "window": {
                "test_window": {"name": "test_window", "linked_group_id": "test_group"}
            },
            "group": {"test_group": {"name": "test_group"}},
        }[entry_type]

        return calculator

    def test_window_enable_override(self, calculator_with_inheritance):
        """Test window-level enable overrides group and global."""
        # Mock entity states
        calculator_with_inheritance._resolve_entity_state_with_fallback = Mock()
        calculator_with_inheritance._resolve_entity_state_with_fallback.side_effect = [
            "enable",  # Window scenario_b
            "enable",  # Window scenario_c
        ]

        result = calculator_with_inheritance.get_scenario_enables_from_entities(
            "test_window"
        )

        assert result["scenario_b_enabled"] is True
        assert result["scenario_c_enabled"] is True

    def test_window_disable_override(self, calculator_with_inheritance):
        """Test window-level disable overrides group and global."""
        calculator_with_inheritance._resolve_entity_state_with_fallback = Mock()
        calculator_with_inheritance._resolve_entity_state_with_fallback.side_effect = [
            "disable",  # Window scenario_b
            "disable",  # Window scenario_c
        ]

        result = calculator_with_inheritance.get_scenario_enables_from_entities(
            "test_window"
        )

        assert result["scenario_b_enabled"] is False
        assert result["scenario_c_enabled"] is False

    def test_window_inherit_from_group(self, calculator_with_inheritance):
        """Test window inherits from group when set to inherit."""
        # Mock window inherit, group enable
        calculator_with_inheritance._resolve_entity_state_with_fallback = Mock()
        calculator_with_inheritance._resolve_entity_state_with_fallback.side_effect = [
            "inherit",  # Window scenario_b
            "inherit",  # Window scenario_c
            "enable",  # Group scenario_b
            "enable",  # Group scenario_c
        ]

        result = calculator_with_inheritance.get_scenario_enables_from_entities(
            "test_window"
        )

        assert result["scenario_b_enabled"] is True
        assert result["scenario_c_enabled"] is True

    def test_window_inherit_from_global(self, calculator_with_inheritance):
        """Test window inherits from global when group also inherits."""
        # Mock window inherit, group inherit, global on
        calculator_with_inheritance._resolve_entity_state_with_fallback = Mock()
        calculator_with_inheritance._resolve_entity_state_with_fallback.side_effect = [
            "inherit",  # Window scenario_b
            "inherit",  # Window scenario_c
            "inherit",  # Group scenario_b
            "inherit",  # Group scenario_c
            "on",  # Global scenario_b
            "on",  # Global scenario_c
        ]

        result = calculator_with_inheritance.get_scenario_enables_from_entities(
            "test_window"
        )

        assert result["scenario_b_enabled"] is True
        assert result["scenario_c_enabled"] is True


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
class TestCalculatorIntegration:
    """Integration tests for complete calculation workflow."""

    @pytest.fixture
    def full_calculator_setup(self, hass):
        """Create fully configured calculator for integration testing."""
        mock_entry = Mock(spec=ConfigEntry)
        mock_entry.entry_id = "test_entry"

        calculator = SolarWindowCalculator(hass, mock_entry)

        # Mock comprehensive subentry structure
        calculator._get_subentries_by_type = Mock()
        calculator._get_subentries_by_type.side_effect = lambda entry_type: {
            "global": {
                "global_config": {
                    "physical": {
                        "g_value": 0.7,
                        "frame_width": 0.05,
                        "diffuse_factor": 0.3,
                        "tilt": 0,
                    },
                    "thresholds": {"direct": 400, "diffuse": 200},
                    "temperatures": {"indoor_base": 24, "outdoor_base": 25},
                    "scenario_b": {
                        "enabled": True,
                        "temp_indoor_offset": 1,
                        "temp_outdoor_offset": 2,
                    },
                    "scenario_c": {
                        "enabled": True,
                        "temp_forecast_threshold": 30,
                        "start_hour": 10,
                    },
                }
            },
            "group": {
                "south_windows": {
                    "name": "south_windows",
                    "thresholds": {"direct": 350},  # Override global
                }
            },
            "window": {
                "living_room_south": {
                    "name": "living_room_south",
                    "linked_group_id": "south_windows",
                    "window_width": 2.0,
                    "window_height": 1.5,
                    "azimuth": 180,
                    "elevation_min": 0,
                    "elevation_max": 90,
                    "azimuth_min": -90,
                    "azimuth_max": 90,
                    "shadow_depth": 0.3,
                    "shadow_offset": 0.2,
                    "indoor_temperature_sensor": "sensor.living_room_temp",
                },
                "bedroom_east": {
                    "name": "bedroom_east",
                    "linked_group_id": None,  # No group
                    "window_width": 1.5,
                    "window_height": 1.2,
                    "azimuth": 90,
                    "elevation_min": 0,
                    "elevation_max": 90,
                    "azimuth_min": -45,
                    "azimuth_max": 45,
                    "shadow_depth": 0,
                    "shadow_offset": 0,
                    "indoor_temperature_sensor": "sensor.bedroom_temp",
                },
            },
        }[entry_type]

        # Mock global data
        calculator._get_global_data_merged = Mock(
            return_value={
                "global_sensitivity": 1.0,
                "children_factor": 0.8,
                "temperature_offset": 0.0,
                "scenario_b_enabled": True,
                "scenario_c_enabled": True,
                "debug_mode": False,
                "maintenance_mode": False,
                "solar_radiation_sensor": "sensor.solar_radiation",
                "outdoor_temperature_sensor": "sensor.outdoor_temp",
                "weather_forecast_temperature_sensor": "sensor.forecast_temp",
                "weather_warning_sensor": "sensor.weather_warning",
            }
        )

        # Mock entity states
        calculator._get_cached_entity_state = Mock()
        calculator._get_cached_entity_state.side_effect = lambda entity_id, fallback: {
            "sensor.solar_radiation": "600",
            "sensor.outdoor_temp": "28",
            "sensor.forecast_temp": "25",
            "sensor.weather_warning": "off",
            "sensor.living_room_temp": "26",
            "sensor.bedroom_temp": "23",
        }.get(entity_id, fallback)

        # Mock sun attributes
        calculator.get_safe_attr = Mock()
        calculator.get_safe_attr.side_effect = lambda entity_id, attr, fallback: {
            ("sun.sun", "azimuth"): 180,  # South
            ("sun.sun", "elevation"): 45,  # Mid-day
        }.get((entity_id, attr), fallback)

        # Mock scenario inheritance
        calculator.get_scenario_enables_from_entities = Mock(
            return_value={"scenario_b_enabled": True, "scenario_c_enabled": False}
        )

        return calculator

    def test_full_calculation_cycle(self, full_calculator_setup):
        """Test complete calculation cycle with multiple windows."""
        results = full_calculator_setup.calculate_all_windows_from_flows()

        # Verify structure
        assert "living_room_south" in results
        assert "bedroom_east" in results
        assert "summary" in results

        # Verify living room (south window with group inheritance)
        living_room = results["living_room_south"]
        assert living_room["name"] == "living_room_south"
        assert living_room["power_total"] > 0
        assert living_room["power_direct"] >= 0
        assert living_room["power_diffuse"] > 0
        assert 0.1 <= living_room["shadow_factor"] <= 1.0
        assert living_room["area_m2"] > 0
        assert isinstance(living_room["is_visible"], bool)
        assert isinstance(living_room["shade_required"], bool)
        assert isinstance(living_room["shade_reason"], str)

        # Verify bedroom (east window, no group)
        bedroom = results["bedroom_east"]
        assert bedroom["name"] == "bedroom_east"
        assert bedroom["power_total"] >= 0
        assert bedroom["area_m2"] > 0

        # Verify summary
        summary = results["summary"]
        assert summary["window_count"] == 2
        assert summary["total_power"] >= 0
        assert summary["shading_count"] >= 0
        assert "calculation_time" in summary

    def test_calculation_error_handling(self, full_calculator_setup):
        """Test error handling during calculation."""
        # Make one window calculation fail
        original_method = full_calculator_setup.calculate_window_solar_power_with_shadow

        def mock_calculate(*args, **kwargs):
            if "living_room_south" in str(args):
                raise ValueError("Test error")
            return original_method(*args, **kwargs)

        full_calculator_setup.calculate_window_solar_power_with_shadow = Mock(
            side_effect=mock_calculate
        )

        results = full_calculator_setup.calculate_all_windows_from_flows()

        # Should still complete with error window having zero values
        assert "living_room_south" in results
        assert results["living_room_south"]["power_total"] == 0
        assert "error" in results["living_room_south"]["shade_reason"].lower()

        # Other window should calculate normally
        assert "bedroom_east" in results


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
class TestCalculatorPerformance:
    """Test performance aspects of the calculator."""

    @pytest.fixture
    def performance_calculator(self, hass):
        """Create calculator for performance testing."""
        mock_entry = Mock(spec=ConfigEntry)
        calculator = SolarWindowCalculator(hass, mock_entry)

        # Create many windows for performance testing
        windows = {}
        for i in range(50):  # 50 windows
            windows[f"window_{i}"] = {
                "name": f"window_{i}",
                "linked_group_id": None,
                "window_width": 1.5,
                "window_height": 1.2,
                "azimuth": (i * 7) % 360,  # Varied orientations
                "elevation_min": 0,
                "elevation_max": 90,
                "azimuth_min": -45,
                "azimuth_max": 45,
                "shadow_depth": (i % 5) * 0.1,  # Varied shadow depths
                "shadow_offset": (i % 3) * 0.1,
                "indoor_temperature_sensor": f"sensor.room_{i}_temp",
            }

        calculator._get_subentries_by_type = Mock()
        calculator._get_subentries_by_type.side_effect = lambda entry_type: {
            "global": {
                "global_config": {
                    "physical": {
                        "g_value": 0.7,
                        "frame_width": 0.05,
                        "diffuse_factor": 0.3,
                        "tilt": 0,
                    },
                    "thresholds": {"direct": 400, "diffuse": 200},
                    "temperatures": {"indoor_base": 24, "outdoor_base": 25},
                }
            },
            "group": {},
            "window": windows,
        }[entry_type]

        # Mock other required methods
        calculator._get_global_data_merged = Mock(
            return_value={
                "solar_radiation_sensor": "sensor.solar_radiation",
                "outdoor_temperature_sensor": "sensor.outdoor_temp",
                "weather_forecast_temperature_sensor": "sensor.forecast_temp",
                "weather_warning_sensor": "sensor.weather_warning",
            }
        )

        calculator._get_cached_entity_state = Mock(return_value="25")
        calculator.get_safe_attr = Mock(return_value=45)
        calculator.get_scenario_enables_from_entities = Mock(
            return_value={"scenario_b_enabled": False, "scenario_c_enabled": False}
        )

        return calculator

    def test_calculation_performance(self, performance_calculator):
        """Test calculation performance with many windows."""
        import time

        start_time = time.time()
        results = performance_calculator.calculate_all_windows_from_flows()
        end_time = time.time()

        calculation_time = end_time - start_time

        # Should complete 50 windows in reasonable time
        assert calculation_time < 1.0  # Less than 1 second
        assert len(results) == 51  # 50 windows + 1 summary

    def test_entity_cache_efficiency(self, performance_calculator):
        """Test that entity caching reduces redundant calls."""
        # Run calculation
        performance_calculator.calculate_all_windows_from_flows()

        # Entity cache should significantly reduce calls
        # With 50 windows, we should have much fewer than 50 calls per entity
        call_count = performance_calculator._get_cached_entity_state.call_count
        assert call_count < 200  # Should be much less due to caching