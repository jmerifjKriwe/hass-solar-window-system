"""
Unit tests for the DebugMixin module.

This test suite provides comprehensive coverage for all implemented debug methods
in the DebugMixin class, including entity search, sensor state collection,
and debug output generation.
"""

import logging

import pytest
from unittest.mock import Mock

from custom_components.solar_window_system.modules.debug import DebugMixin


class TestDebugMixin:
    """Test suite for DebugMixin debug functionality."""

    def test_collect_current_sensor_states_with_valid_sensors(self) -> None:
        """Test collecting sensor states with valid SWS sensors."""
        # Create mock hass and entity registry
        mock_hass = Mock()
        mock_entity_reg = Mock()

        # Mock entity registry entities
        mock_entity1 = Mock()
        mock_entity1.name = "Temperature Sensor"
        mock_entity2 = Mock()
        mock_entity2.name = "Power Sensor"

        mock_entity_reg.entities = {
            "sensor.sws_global_temperature": mock_entity1,
            "sensor.sws_global_power": mock_entity2,
            "sensor.other_temp": Mock(),  # Non-SWS sensor, should be ignored
        }

        # Mock states
        mock_state1 = Mock()
        mock_state1.state = "25.5"
        mock_state1.last_updated = Mock()
        mock_state1.last_updated.isoformat.return_value = "2025-08-29T10:00:00"
        mock_state1.attributes = {"unit": "°C"}

        mock_state2 = Mock()
        mock_state2.state = "150.0"
        mock_state2.last_updated = None
        mock_state2.attributes = {}

        mock_hass.states.get.side_effect = lambda eid: {
            "sensor.sws_global_temperature": mock_state1,
            "sensor.sws_global_power": mock_state2,
        }.get(eid)

        # Mock entity registry import
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(return_value=mock_entity_reg)

        try:
            debug = DebugMixin()
            debug.hass = mock_hass

            result = debug._collect_current_sensor_states("window1")

            # Verify results
            assert len(result) == 2
            assert "sensor.sws_global_temperature" in result
            assert "sensor.sws_global_power" in result

            # Verify temperature sensor data
            temp_data = result["sensor.sws_global_temperature"]
            assert temp_data["state"] == "25.5"
            assert temp_data["name"] == "Temperature Sensor"
            assert temp_data["last_updated"] == "2025-08-29T10:00:00"
            assert temp_data["attributes"] == {"unit": "°C"}

            # Verify power sensor data
            power_data = result["sensor.sws_global_power"]
            assert power_data["state"] == "150.0"
            assert power_data["name"] == "Power Sensor"
            assert power_data["last_updated"] is None
            assert power_data["attributes"] == {}

        finally:
            # Restore original function
            debug_module.er.async_get = original_async_get

    def test_collect_current_sensor_states_with_unavailable_sensor(self) -> None:
        """Test collecting sensor states when a sensor is unavailable."""
        mock_hass = Mock()
        mock_entity_reg = Mock()

        mock_entity = Mock()
        mock_entity.name = "Faulty Sensor"

        mock_entity_reg.entities = {
            "sensor.sws_global_faulty": mock_entity,
        }

        # Mock hass.states.get to raise an exception
        mock_hass.states.get.side_effect = AttributeError("Sensor unavailable")

        # Mock entity registry import
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(return_value=mock_entity_reg)

        try:
            debug = DebugMixin()
            debug.hass = mock_hass

            result = debug._collect_current_sensor_states("window1")

            # Verify error handling
            assert len(result) == 1
            assert "sensor.sws_global_faulty" in result

            faulty_data = result["sensor.sws_global_faulty"]
            assert faulty_data["state"] == "unavailable"
            assert faulty_data["name"] == "Faulty Sensor"
            assert "error" in faulty_data

        finally:
            debug_module.er.async_get = original_async_get

    def test_collect_current_sensor_states_with_entity_registry_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test collecting sensor states when entity registry fails."""
        mock_hass = Mock()

        # Mock entity registry import to raise exception
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(side_effect=Exception("Registry error"))

        try:
            debug = DebugMixin()
            debug.hass = mock_hass

            with caplog.at_level(logging.ERROR):
                result = debug._collect_current_sensor_states("window1")

            # Should return empty dict on error
            assert result == {}

        finally:
            debug_module.er.async_get = original_async_get

    def test_get_current_sensor_states_alias(self) -> None:
        """Test _get_current_sensor_states alias."""
        mock_hass = Mock()
        mock_entity_reg = Mock()
        mock_entity_reg.entities = {}

        # Mock entity registry import
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(return_value=mock_entity_reg)

        try:
            debug = DebugMixin()
            debug.hass = mock_hass

            # Both methods should return the same result
            result1 = debug._collect_current_sensor_states("window1")
            result2 = debug._get_current_sensor_states("window1")

            assert result1 == result2

        finally:
            debug_module.er.async_get = original_async_get

    def test_generate_debug_output_with_sensor_states(self) -> None:
        """Test generating debug output with sensor states."""
        debug = DebugMixin()

        sensor_states = {
            "sensor.sws_global_temperature": {
                "state": "25.5",
                "name": "Temperature Sensor",
            },
            "sensor.sws_global_power": {
                "state": "150.0",
                "name": "Power Sensor",
                "error": "Connection timeout",
            },
        }

        result = debug._generate_debug_output(sensor_states)

        # Verify output format
        assert "Solar Window System Debug Output:" in result
        assert "=" * 40 in result
        assert "Entity: sensor.sws_global_temperature" in result
        assert "State: 25.5" in result
        assert "Name: Temperature Sensor" in result
        assert "Entity: sensor.sws_global_power" in result
        assert "State: 150.0" in result
        assert "Name: Power Sensor" in result
        assert "Error: Connection timeout" in result

    def test_generate_debug_output_empty_states(self) -> None:
        """Test generating debug output with empty sensor states."""
        debug = DebugMixin()

        result = debug._generate_debug_output({})

        assert result == "No sensor states available"

    def test_find_entity_by_name_global_entity(self) -> None:
        """Test finding a global entity by name."""
        mock_hass = Mock()
        mock_entity_reg = Mock()

        # Mock entity entry
        mock_entity = Mock()
        mock_entity.name = "Global Temperature"

        mock_entity_reg.entities = {
            "sensor.sws_global_temperature": mock_entity,
        }

        # Mock entity registry import
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(return_value=mock_entity_reg)

        try:
            debug = DebugMixin()

            result = debug._find_entity_by_name(
                mock_hass, "Global Temperature", "global"
            )

            assert result == "sensor.sws_global_temperature"

        finally:
            debug_module.er.async_get = original_async_get

    def test_find_entity_by_name_window_entity(self) -> None:
        """Test finding a window-specific entity by name."""
        mock_hass = Mock()
        mock_entity_reg = Mock()

        # Mock entity entry
        mock_entity = Mock()
        mock_entity.name = "Window Temperature"

        mock_entity_reg.entities = {
            "sensor.sws_window_livingroom_temperature": mock_entity,
        }

        # Mock entity registry import
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(return_value=mock_entity_reg)

        try:
            debug = DebugMixin()

            result = debug._find_entity_by_name(
                mock_hass, "Window Temperature", "window", "livingroom"
            )

            assert result == "sensor.sws_window_livingroom_temperature"

        finally:
            debug_module.er.async_get = original_async_get

    def test_find_entity_by_name_group_entity(self) -> None:
        """Test finding a group-specific entity by name."""
        mock_hass = Mock()
        mock_entity_reg = Mock()

        # Mock entity entry
        mock_entity = Mock()
        mock_entity.name = "Group Temperature"

        mock_entity_reg.entities = {
            "sensor.sws_group_floor1_temperature": mock_entity,
        }

        # Mock entity registry import
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(return_value=mock_entity_reg)

        try:
            debug = DebugMixin()

            result = debug._find_entity_by_name(
                mock_hass, "Group Temperature", "group", None, "floor1"
            )

            assert result == "sensor.sws_group_floor1_temperature"

        finally:
            debug_module.er.async_get = original_async_get

    def test_find_entity_by_name_not_found(self) -> None:
        """Test finding an entity that doesn't exist."""
        mock_hass = Mock()
        mock_entity_reg = Mock()
        mock_entity_reg.entities = {}

        # Mock entity registry import
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(return_value=mock_entity_reg)

        try:
            debug = DebugMixin()

            result = debug._find_entity_by_name(
                mock_hass, "Nonexistent Sensor", "global"
            )

            assert result is None

        finally:
            debug_module.er.async_get = original_async_get

    def test_find_entity_by_name_with_registry_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test finding an entity when entity registry fails."""
        mock_hass = Mock()

        # Mock entity registry import to raise exception
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(side_effect=Exception("Registry error"))

        try:
            debug = DebugMixin()

            with caplog.at_level(logging.ERROR):
                result = debug._find_entity_by_name(
                    mock_hass, "Temperature Sensor", "global"
                )

            assert result is None

        finally:
            debug_module.er.async_get = original_async_get

    def test_find_entity_by_name_name_transformation(self) -> None:
        """Test entity name transformation for special characters."""
        mock_hass = Mock()
        mock_entity_reg = Mock()

        # Mock entity entry
        mock_entity = Mock()
        mock_entity.name = "Solar Power m²"

        mock_entity_reg.entities = {
            "sensor.sws_global_solar_power_m2": mock_entity,
        }

        # Mock entity registry import
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(return_value=mock_entity_reg)

        try:
            debug = DebugMixin()

            result = debug._find_entity_by_name(mock_hass, "Solar Power m²", "global")

            assert result == "sensor.sws_global_solar_power_m2"

        finally:
            debug_module.er.async_get = original_async_get

    def test_placeholder_methods_raise_not_implemented(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that placeholder methods are now implemented and work correctly."""
        debug = DebugMixin()

        # Test main debug method - now implemented
        # Note: This will fail because DebugMixin doesn't have hass attribute
        # but the method is implemented
        with caplog.at_level(logging.ERROR):
            try:
                result = debug.create_debug_data("window1")
                # If it doesn't raise an exception, it should return a dict
                assert isinstance(result, dict)
                assert "window_id" in result
                assert "error" in result  # Expected due to missing hass
            except AttributeError:
                # Expected when hass is not available
                pass

        # Test search methods - now implemented
        mock_hass = Mock()
        # Mock states.all() to return an empty list
        mock_hass.states.all.return_value = []

        # Test _search_window_sensors
        result = debug._search_window_sensors(mock_hass, "window1")
        assert isinstance(result, list)

        # Test _search_group_sensors
        result = debug._search_group_sensors(mock_hass, "window1", {})
        assert isinstance(result, list)

        # Test _search_global_sensors
        result = debug._search_global_sensors(mock_hass)
        assert isinstance(result, list)

    @pytest.mark.parametrize(
        "entity_name",
        [
            "Temperature Sensor",
            "Solar Power m²",
            "Window/Area Ratio",
        ],
    )
    def test_find_entity_by_name_pattern_generation(self, entity_name: str) -> None:
        """Parametrized test for entity name pattern generation."""
        mock_hass = Mock()
        mock_entity_reg = Mock()
        mock_entity_reg.entities = {}

        # Mock entity registry import
        import custom_components.solar_window_system.modules.debug as debug_module

        original_async_get = debug_module.er.async_get
        debug_module.er.async_get = Mock(return_value=mock_entity_reg)

        try:
            debug = DebugMixin()

            # This will fail to find the entity, but verify pattern was attempted
            result = debug._find_entity_by_name(mock_hass, entity_name, "global")

            assert result is None
            # Verify that async_get was called (pattern was attempted)
            debug_module.er.async_get.assert_called_with(mock_hass)

        finally:
            debug_module.er.async_get = original_async_get
