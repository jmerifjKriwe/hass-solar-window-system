"""
Unit tests for the UtilsMixin module.

This test suite provides comprehensive coverage for all implemented utility
methods in the UtilsMixin class, including edge cases, error handling, and
various input scenarios.
"""

import pytest
from typing import Any
from unittest.mock import Mock

from custom_components.solar_window_system.modules.utils import UtilsMixin


class TestUtilsMixin:
    """Test suite for UtilsMixin utility methods."""

    def test_validate_temperature_range_valid_inputs(self) -> None:
        """Test temperature validation with valid inputs."""
        utils = UtilsMixin()

        # Test normal temperature range
        assert utils._validate_temperature_range(20.0) is True
        assert utils._validate_temperature_range(0.0) is True
        assert utils._validate_temperature_range(-30.0) is True
        assert utils._validate_temperature_range(50.0) is True

        # Test integer inputs
        assert utils._validate_temperature_range(25) is True
        assert utils._validate_temperature_range(-10) is True

    def test_validate_temperature_range_boundary_values(self) -> None:
        """Test temperature validation at boundary values."""
        utils = UtilsMixin()

        # Test exact boundary values
        assert utils._validate_temperature_range(-50.0) is True  # Minimum
        assert utils._validate_temperature_range(60.0) is True  # Maximum

        # Test just outside boundaries
        assert utils._validate_temperature_range(-50.1) is False  # Below minimum
        assert utils._validate_temperature_range(60.1) is False  # Above maximum

    def test_validate_temperature_range_custom_ranges(self) -> None:
        """Test temperature validation with custom min/max ranges."""
        utils = UtilsMixin()

        # Test with custom range
        assert (
            utils._validate_temperature_range(15.0, min_temp=10.0, max_temp=20.0)
            is True
        )
        assert (
            utils._validate_temperature_range(5.0, min_temp=10.0, max_temp=20.0)
            is False
        )
        assert (
            utils._validate_temperature_range(25.0, min_temp=10.0, max_temp=20.0)
            is False
        )

    def test_validate_temperature_range_invalid_types(self) -> None:
        """Test temperature validation with invalid input types."""
        utils = UtilsMixin()

        # Test invalid types
        assert utils._validate_temperature_range("25.0") is False
        assert utils._validate_temperature_range(None) is False
        assert utils._validate_temperature_range([]) is False
        assert utils._validate_temperature_range({}) is False

    def test_validate_temperature_range_special_values(self) -> None:
        """Test temperature validation with special float values."""
        utils = UtilsMixin()

        # Test special float values
        assert utils._validate_temperature_range(float("nan")) is False
        assert utils._validate_temperature_range(float("inf")) is False
        assert utils._validate_temperature_range(float("-inf")) is False

    def test_safe_float_conversion_valid_inputs(self) -> None:
        """Test safe float conversion with valid inputs."""
        utils = UtilsMixin()

        # Test valid numeric strings
        assert utils._safe_float_conversion("25.5") == 25.5
        assert utils._safe_float_conversion("0") == 0.0
        assert utils._safe_float_conversion("-10.5") == -10.5

        # Test numeric types
        assert utils._safe_float_conversion(42) == 42.0
        assert utils._safe_float_conversion(3.14) == 3.14

    def test_safe_float_conversion_special_cases(self) -> None:
        """Test safe float conversion with special cases."""
        utils = UtilsMixin()

        # Test special string values that should return default
        assert utils._safe_float_conversion("") == 0.0  # Default
        assert utils._safe_float_conversion(None) == 0.0
        assert utils._safe_float_conversion("inherit") == 0.0
        assert utils._safe_float_conversion("-1") == 0.0
        assert utils._safe_float_conversion(-1) == 0.0

        # Test with custom default
        assert utils._safe_float_conversion("", default=5.0) == 5.0
        assert utils._safe_float_conversion("inherit", default=-999.0) == -999.0

    def test_safe_float_conversion_invalid_inputs(self) -> None:
        """Test safe float conversion with invalid inputs."""
        utils = UtilsMixin()

        # Test invalid string values
        assert utils._safe_float_conversion("not_a_number") == 0.0
        assert utils._safe_float_conversion("25.5.5") == 0.0
        # Note: "NaN" string gets converted to float('nan') by Python's float()
        # The function should return the NaN value, not 0.0
        import math

        result = utils._safe_float_conversion("NaN")
        assert math.isnan(result)

        # Test complex types
        assert utils._safe_float_conversion([]) == 0.0
        assert utils._safe_float_conversion({}) == 0.0
        assert utils._safe_float_conversion(object()) == 0.0

    def test_get_safe_state_valid_entity(self) -> None:
        """Test getting safe state from valid entity."""
        utils = UtilsMixin()

        # Mock Home Assistant and entity state
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_hass.states.get.return_value = mock_state

        result = utils.get_safe_state(mock_hass, "sensor.temperature")
        assert result == "25.5"
        mock_hass.states.get.assert_called_once_with("sensor.temperature")

    def test_get_safe_state_unavailable_entity(self) -> None:
        """Test getting safe state from unavailable entity."""
        utils = UtilsMixin()

        # Mock Home Assistant with unavailable entity
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "unavailable"
        mock_hass.states.get.return_value = mock_state

        result = utils.get_safe_state(mock_hass, "sensor.temperature", default=20.0)
        assert result == 20.0

    def test_get_safe_state_unknown_entity(self) -> None:
        """Test getting safe state from unknown entity."""
        utils = UtilsMixin()

        # Mock Home Assistant with unknown entity
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "unknown"
        mock_hass.states.get.return_value = mock_state

        result = utils.get_safe_state(mock_hass, "sensor.temperature", default="N/A")
        assert result == "N/A"

    def test_get_safe_state_none_entity(self) -> None:
        """Test getting safe state when entity doesn't exist."""
        utils = UtilsMixin()

        # Mock Home Assistant with None entity
        mock_hass = Mock()
        mock_hass.states.get.return_value = None

        result = utils.get_safe_state(mock_hass, "sensor.nonexistent", default=0)
        assert result == 0

    def test_get_safe_state_empty_entity_id(self) -> None:
        """Test getting safe state with empty entity ID."""
        utils = UtilsMixin()

        mock_hass = Mock()
        result = utils.get_safe_state(mock_hass, "", default=15.0)
        assert result == 15.0
        mock_hass.states.get.assert_not_called()

    def test_get_safe_state_exception_handling(self) -> None:
        """Test getting safe state with exception handling."""
        utils = UtilsMixin()

        # Mock Home Assistant that raises exception
        mock_hass = Mock()
        mock_hass.states.get.side_effect = AttributeError("Test error")

        result = utils.get_safe_state(mock_hass, "sensor.temperature", default=-1)
        assert result == -1

    def test_get_safe_attr_valid_entity(self) -> None:
        """Test getting safe attribute from valid entity."""
        utils = UtilsMixin()

        # Mock Home Assistant and entity state with attributes
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_state.attributes = {"unit": "°C", "friendly_name": "Temperature"}
        mock_hass.states.get.return_value = mock_state

        result = utils.get_safe_attr(mock_hass, "sensor.temperature", "unit")
        assert result == "°C"

    def test_get_safe_attr_missing_attribute(self) -> None:
        """Test getting safe attribute when attribute doesn't exist."""
        utils = UtilsMixin()

        # Mock Home Assistant with entity that has no requested attribute
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_state.attributes = {"friendly_name": "Temperature"}
        mock_hass.states.get.return_value = mock_state

        result = utils.get_safe_attr(
            mock_hass, "sensor.temperature", "unit", default="N/A"
        )
        assert result == "N/A"

    def test_get_safe_attr_unavailable_entity(self) -> None:
        """Test getting safe attribute from unavailable entity."""
        utils = UtilsMixin()

        # Mock Home Assistant with unavailable entity
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "unavailable"
        mock_state.attributes = {}
        mock_hass.states.get.return_value = mock_state

        result = utils.get_safe_attr(
            mock_hass, "sensor.temperature", "unit", default="default_unit"
        )
        assert result == "default_unit"

    def test_get_safe_attr_none_entity(self) -> None:
        """Test getting safe attribute when entity doesn't exist."""
        utils = UtilsMixin()

        # Mock Home Assistant with None entity
        mock_hass = Mock()
        mock_hass.states.get.return_value = None

        result = utils.get_safe_attr(mock_hass, "sensor.nonexistent", "unit", default=0)
        assert result == 0

    def test_get_safe_attr_empty_entity_id(self) -> None:
        """Test getting safe attribute with empty entity ID."""
        utils = UtilsMixin()

        mock_hass = Mock()
        result = utils.get_safe_attr(mock_hass, "", "unit", default="empty")
        assert result == "empty"
        mock_hass.states.get.assert_not_called()

    def test_get_safe_attr_exception_handling(self) -> None:
        """Test getting safe attribute with exception handling."""
        utils = UtilsMixin()

        # Mock Home Assistant that raises exception
        mock_hass = Mock()
        mock_hass.states.get.side_effect = KeyError("Test error")

        result = utils.get_safe_attr(
            mock_hass, "sensor.temperature", "unit", default=-999
        )
        assert result == -999

    def test_placeholder_methods_raise_not_implemented(self) -> None:
        """Test that placeholder methods are now implemented and work correctly."""
        utils = UtilsMixin()

        # Test _format_debug_value implementation
        result = utils._format_debug_value(25.5)
        assert isinstance(result, str)
        assert "25.5" in result

        result = utils._format_debug_value("test_value")
        assert isinstance(result, str)
        assert "test_value" in result

        # Test _calculate_time_difference_minutes implementation
        result = utils._calculate_time_difference_minutes("10:00", "11:00")
        assert result == 60.0  # 1 hour = 60 minutes

        result = utils._calculate_time_difference_minutes("10:30", "11:15")
        assert result == 45.0  # 45 minutes

        # Test _is_valid_entity_state implementation
        assert utils._is_valid_entity_state("25.5") is True
        assert utils._is_valid_entity_state("unavailable") is False
        assert utils._is_valid_entity_state("unknown") is False
        assert utils._is_valid_entity_state(None) is False

    @pytest.mark.parametrize("temp", [20.0, -50.0, 60.0])
    def test_validate_temperature_range_parametrized_valid(self, temp: float) -> None:
        """Parametrized test for valid temperature values."""
        utils = UtilsMixin()
        assert utils._validate_temperature_range(temp) is True

    @pytest.mark.parametrize("temp", [-50.1, 60.1, float("nan"), float("inf")])
    def test_validate_temperature_range_parametrized_invalid(self, temp: float) -> None:
        """Parametrized test for invalid temperature values."""
        utils = UtilsMixin()
        assert utils._validate_temperature_range(temp) is False

    @pytest.mark.parametrize(
        ("input_val", "expected"),
        [
            ("25.5", 25.5),
            ("0", 0.0),
            ("", 0.0),
            (None, 0.0),
            ("inherit", 0.0),
            ("not_a_number", 0.0),
            (42, 42.0),
            (3.14, 3.14),
        ],
    )
    def test_safe_float_conversion_parametrized(
        self, input_val: Any, expected: float
    ) -> None:
        """Parametrized test for safe float conversion."""
        utils = UtilsMixin()
        assert utils._safe_float_conversion(input_val) == expected
