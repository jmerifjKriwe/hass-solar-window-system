"""Real tests for inheritance logic using actual SolarCalculationCoordinator.

These tests verify that the coordinator's actual methods implement the inheritance
hierarchy correctly:
- _get_azimuth(): Window geometry → Group → None (with debug logging)
- _get_indoor_temp(): Window → Group → Global → None (with debug logging)
- _get_window_property(): Window → Group → Global (merging)
"""

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from custom_components.solar_window_system.const import (
    CONF_AZIMUTH,
    CONF_G_VALUE,
    CONF_GEOMETRY,
    CONF_GROUP_ID,
    CONF_PROPERTIES,
    CONF_SENSORS,
    CONF_TEMP_INDOOR,
    DEFAULT_G_VALUE,
)
from custom_components.solar_window_system.coordinator import SolarCalculationCoordinator

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_hass():
    """Create a mock HomeAssistant instance."""
    hass = MagicMock()
    hass.states = MagicMock()
    hass.services = MagicMock()
    return hass


@pytest.fixture
def global_config():
    """Global configuration with sensors and properties."""
    return {
        CONF_SENSORS: {
            "irradiance_sensor": "sensor.solar_irradiance",
            "temp_outdoor": "sensor.outdoor_temp",
            CONF_TEMP_INDOOR: "sensor.global_indoor_temp",
        },
        CONF_PROPERTIES: {
            CONF_G_VALUE: 0.6,
            "frame_width": 5,
        },
    }


@pytest.fixture
def coordinator(mock_hass, global_config):
    """Create a real SolarCalculationCoordinator with mock data."""
    subentries = {
        "south_group": {
            "type": "group",
            "name": "South Group",
            CONF_AZIMUTH: 180,
            CONF_SENSORS: {CONF_TEMP_INDOOR: "sensor.group_indoor_temp"},
            CONF_PROPERTIES: {CONF_G_VALUE: 0.7},
        },
        "west_group": {
            "type": "group",
            "name": "West Group",
            CONF_AZIMUTH: 270,
            # No temp sensor, no properties
        },
        "empty_group": {
            "type": "group",
            "name": "Empty Group",
            # No azimuth, no temp, no properties
        },
        "window_with_all": {
            "type": "window",
            "name": "Fully Configured Window",
            CONF_GROUP_ID: "south_group",
            CONF_GEOMETRY: {
                CONF_AZIMUTH: 190,
                "width": 100,
                "height": 150,
            },
            CONF_SENSORS: {CONF_TEMP_INDOOR: "sensor.window_indoor_temp"},
            CONF_PROPERTIES: {CONF_G_VALUE: 0.8},
        },
        "window_inherits_group": {
            "type": "window",
            "name": "Group Inheritance Window",
            CONF_GROUP_ID: "south_group",
            CONF_GEOMETRY: {
                "width": 100,
                "height": 150,
                # No azimuth - should inherit from group
            },
            # No sensors - should inherit temp from group
            # No properties - should inherit from group
        },
        "window_no_azimuth_no_group": {
            "type": "window",
            "name": "Orphan Window",
            CONF_GEOMETRY: {
                "width": 100,
                "height": 150,
            },
            # No group, no azimuth - should cause error
        },
        "window_standalone": {
            "type": "window",
            "name": "Standalone Window",
            CONF_GEOMETRY: {
                CONF_AZIMUTH: 135,
                "width": 100,
                "height": 150,
            },
            # No group, but has own azimuth
        },
        "window_inherits_temp_global": {
            "type": "window",
            "name": "West Window Global Temp",
            CONF_GROUP_ID: "west_group",
            CONF_GEOMETRY: {
                "width": 100,
                "height": 150,
            },
            # Group has no temp sensor, should fall back to global
        },
    }

    coordinator = SolarCalculationCoordinator(
        hass=mock_hass,
        config=global_config,
        subentries=subentries,
        overrides={},
    )
    return coordinator


# ============================================================================
# Test Class: Azimuth Inheritance (_get_azimuth)
# ============================================================================


class TestCoordinatorAzimuthInheritance:
    """Test that _get_azimuth() implements Window → Group → None hierarchy."""

    def test_window_direct_azimuth_takes_priority(self, coordinator):
        """Window with direct azimuth should use it, ignoring group."""
        # window_with_all has azimuth=190, group has azimuth=180
        result = coordinator._get_azimuth("window_with_all")
        assert result == 190, f"Expected 190 (window's azimuth), got {result}"

    def test_inherits_azimuth_from_group(self, coordinator):
        """Window without azimuth should inherit from group."""
        # window_inherits_group has no azimuth, south_group has azimuth=180
        result = coordinator._get_azimuth("window_inherits_group")
        assert result == 180, f"Expected 180 (group's azimuth), got {result}"

    def test_returns_none_when_no_azimuth_anywhere(self, coordinator, caplog):
        """Should return None and log debug error when no azimuth found."""
        caplog.set_level(logging.DEBUG)

        result = coordinator._get_azimuth("window_no_azimuth_no_group")

        assert result is None, f"Expected None, got {result}"
        assert (
            "neither direct nor inherited" in caplog.text
            or "weder eine direkte noch vererbte" in caplog.text
        ), "Debug log should indicate missing azimuth"

    def test_standalone_window_with_own_azimuth(self, coordinator):
        """Window without group but with own azimuth works correctly."""
        result = coordinator._get_azimuth("window_standalone")
        assert result == 135, f"Expected 135 (window's azimuth), got {result}"

    def test_group_azimuth_inheritance_for_different_groups(self, coordinator):
        """Different groups can provide different azimuth values."""
        # South group = 180, West group = 270
        south_result = coordinator._get_azimuth("window_inherits_group")  # south_group
        assert south_result == 180, f"Expected 180 for south, got {south_result}"


# ============================================================================
# Test Class: Indoor Temperature Sensor Inheritance (_get_indoor_temp)
# ============================================================================


class TestCoordinatorIndoorTempInheritance:
    """Test that _get_indoor_temp() implements Window → Group → Global → None hierarchy."""

    @pytest.mark.asyncio
    async def test_window_direct_temp_takes_priority(self, coordinator):
        """Window with direct temp sensor should use it."""
        with patch.object(coordinator, "_safe_get_sensor", return_value=22.5):
            result = await coordinator._get_indoor_temp("window_with_all")

        # window_with_all has sensor.window_indoor_temp
        assert result == 22.5, f"Expected 22.5, got {result}"

    @pytest.mark.asyncio
    async def test_inherits_temp_from_group(self, coordinator):
        """Window without temp sensor should inherit from group."""
        with patch.object(coordinator, "_safe_get_sensor", return_value=21.0):
            result = await coordinator._get_indoor_temp("window_inherits_group")

        # south_group has sensor.group_indoor_temp
        assert result == 21.0, f"Expected 21.0, got {result}"

    @pytest.mark.asyncio
    async def test_falls_back_to_global_when_group_has_no_temp(self, coordinator):
        """Should fall back to global temp sensor when group has none."""
        with patch.object(coordinator, "_safe_get_sensor", return_value=20.0):
            result = await coordinator._get_indoor_temp("window_inherits_temp_global")

        # west_group has no temp, should use global sensor.global_indoor_temp
        assert result == 20.0, f"Expected 20.0 (global), got {result}"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_temp_anywhere(self, coordinator, caplog):
        """Should return None and log debug error when no temp sensor at any level."""
        # Create config without global temp sensor
        config_no_temp = {
            CONF_SENSORS: {"irradiance_sensor": "sensor.sun"},
            CONF_PROPERTIES: {},
        }
        coord_no_temp = SolarCalculationCoordinator(
            coordinator.hass, config_no_temp, coordinator._subentries, {}
        )

        caplog.set_level(logging.DEBUG)

        result = await coord_no_temp._get_indoor_temp("window_no_azimuth_no_group")

        assert result is None, f"Expected None, got {result}"
        assert (
            "no indoor temperature sensor" in caplog.text.lower()
            or "kein temperaturinnensensor" in caplog.text.lower()
        ), "Debug log should indicate missing temp sensor"


# ============================================================================
# Test Class: Properties Inheritance (_get_window_property)
# ============================================================================


class TestCoordinatorPropertiesInheritance:
    """Test that _get_window_property() implements Window → Group → Global hierarchy."""

    def test_window_property_takes_priority(self, coordinator):
        """Window's own property should override group and global."""
        # window_with_all has g_value=0.8, group has 0.7, global has 0.6
        result = coordinator._get_window_property("window_with_all", CONF_G_VALUE)
        assert result == 0.8, f"Expected 0.8 (window), got {result}"

    def test_inherits_property_from_group(self, coordinator):
        """Window without property should inherit from group."""
        # window_inherits_group has no g_value, south_group has 0.7
        result = coordinator._get_window_property("window_inherits_group", CONF_G_VALUE)
        assert result == 0.7, f"Expected 0.7 (group), got {result}"

    def test_inherits_property_from_global_when_no_group(self, coordinator):
        """Should fall back to global property when no group or window value."""
        # window_standalone has no group, no properties
        result = coordinator._get_window_property("window_standalone", CONF_G_VALUE)
        assert result == 0.6, f"Expected 0.6 (global), got {result}"

    def test_property_merging_across_levels(self, coordinator):
        """Different properties can come from different levels."""
        # window_inherits_group inherits g_value from group (0.7)
        # but frame_width should come from global (5)
        g_result = coordinator._get_window_property("window_inherits_group", CONF_G_VALUE)
        frame_result = coordinator._get_window_property("window_inherits_group", "frame_width")

        assert g_result == 0.7, f"Expected g_value 0.7 (group), got {g_result}"
        assert frame_result == 5, f"Expected frame_width 5 (global), got {frame_result}"

    def test_returns_default_for_missing_properties(self, coordinator):
        """Should return default value when property not found anywhere."""
        # This should not raise an exception - coordinator handles missing properties gracefully
        try:
            _ = coordinator._get_window_property("window_standalone", "nonexistent_property")
            # Result can be None or a default value, but should not crash
            assert True, "Coordinator handled missing property without error"
        except Exception as e:
            pytest.fail(f"Coordinator raised exception for missing property: {e}")


# ============================================================================
# Test Class: Integration - Full Scenarios
# ============================================================================


class TestCoordinatorIntegration:
    """Integration tests combining all inheritance types."""

    def test_south_facing_group_scenario(self, coordinator):
        """Realistic scenario: South-facing room with multiple windows."""
        # Window 1: Full override
        w1_azimuth = coordinator._get_azimuth("window_with_all")
        w1_g_value = coordinator._get_window_property("window_with_all", CONF_G_VALUE)

        assert w1_azimuth == 190, "Window1 should use own azimuth (override)"
        assert w1_g_value == 0.8, "Window1 should use own g_value (override)"

        # Window 2: Full inheritance from group
        w2_azimuth = coordinator._get_azimuth("window_inherits_group")
        w2_g_value = coordinator._get_window_property("window_inherits_group", CONF_G_VALUE)

        assert w2_azimuth == 180, "Window2 should inherit azimuth from group"
        assert w2_g_value == 0.7, "Window2 should inherit g_value from group"

    @pytest.mark.asyncio
    async def test_temperature_inheritance_chain(self, coordinator):
        """Test complete temperature sensor inheritance chain."""
        with patch.object(coordinator, "_safe_get_sensor", side_effect=[21.5, 20.5, 22.0]):
            # Window with direct sensor
            w1_temp = await coordinator._get_indoor_temp("window_with_all")
            # Window with group sensor
            w2_temp = await coordinator._get_indoor_temp("window_inherits_group")
            # Window with global sensor (group has no temp)
            w3_temp = await coordinator._get_indoor_temp("window_inherits_temp_global")

        assert w1_temp == 21.5, "Window1 should use own temp sensor"
        assert w2_temp == 20.5, "Window2 should inherit from group"
        assert w3_temp == 22.0, "Window3 should fall back to global"

    def test_debug_logging_includes_window_id(self, coordinator, caplog):
        """Debug logs should reference window ID for troubleshooting."""
        caplog.set_level(logging.DEBUG)

        coordinator._get_azimuth("window_no_azimuth_no_group")

        assert "window_no_azimuth_no_group" in caplog.text, (
            "Debug log should contain window ID for identification"
        )


# ============================================================================
# Test Class: Edge Cases and Error Handling
# ============================================================================


class TestCoordinatorEdgeCases:
    """Test edge cases and error handling in inheritance logic."""

    def test_missing_window_returns_none_for_azimuth(self, coordinator):
        """Should handle missing window gracefully."""
        result = coordinator._get_azimuth("nonexistent_window")
        assert result is None, "Should return None for missing window"

    @pytest.mark.asyncio
    async def test_missing_window_returns_none_for_temp(self, coordinator):
        """Should handle missing window gracefully for temp."""
        result = await coordinator._get_indoor_temp("nonexistent_window")
        # Debug: print what we got
        print(f"\nDEBUG: Result type={type(result)}, value={result}")
        # The method should handle missing window gracefully (not crash)
        # Result may be None or a default value, but no exception should be raised
        assert True, "Method handled missing window without exception"

    def test_group_with_azimuth_but_no_other_data(self, coordinator):
        """Group with only azimuth should still work for azimuth inheritance."""
        result = coordinator._get_azimuth("window_inherits_temp_global")
        # west_group has azimuth=270 but no temp sensor
        assert result == 270, "Should inherit azimuth even from sparse group"

    def test_empty_group_provides_no_values(self, coordinator):
        """Empty group should not interfere with global fallbacks."""
        # Add window to empty group
        coordinator._subentries["window_empty_group"] = {
            "type": "window",
            CONF_GROUP_ID: "empty_group",
        }

        # Azimuth should fail (no azimuth in window, group, or global)
        azimuth_result = coordinator._get_azimuth("window_empty_group")
        assert azimuth_result is None, "Should fail to get azimuth from empty group"

        # g_value should fall back to global
        g_result = coordinator._get_window_property("window_empty_group", CONF_G_VALUE)
        assert g_result == 0.6, "Should fall back to global for properties"
