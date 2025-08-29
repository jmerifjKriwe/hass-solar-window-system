"""
Tests for flow_integration module.

This module tests the flow-based integration and configuration handling
functionality including data classes and mixin methods.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from custom_components.solar_window_system.modules.flow_integration import (
    FlowIntegrationMixin,
    ShadeRequestFlow,
    WindowCalculationResult,
)


class TestWindowCalculationResult:
    """Test cases for WindowCalculationResult dataclass."""

    def test_window_calculation_result_creation(self) -> None:
        """Test basic creation of WindowCalculationResult."""
        result = WindowCalculationResult(
            power_total=100.0,
            power_direct=70.0,
            power_diffuse=30.0,
            power_direct_raw=75.0,
            power_diffuse_raw=35.0,
            power_total_raw=110.0,
            shadow_factor=0.8,
            is_visible=True,
            area_m2=2.5,
        )

        assert result.power_total == 100.0
        assert result.power_direct == 70.0
        assert result.power_diffuse == 30.0
        assert result.power_direct_raw == 75.0
        assert result.power_diffuse_raw == 35.0
        assert result.power_total_raw == 110.0
        assert result.shadow_factor == 0.8
        assert result.is_visible is True
        assert result.area_m2 == 2.5
        assert result.shade_required is False
        assert result.shade_reason == ""
        assert result.effective_threshold == 0.0

    def test_window_calculation_result_with_shading(self) -> None:
        """Test WindowCalculationResult with shading requirements."""
        result = WindowCalculationResult(
            power_total=150.0,
            power_direct=120.0,
            power_diffuse=30.0,
            power_direct_raw=125.0,
            power_diffuse_raw=35.0,
            power_total_raw=160.0,
            shadow_factor=0.9,
            is_visible=True,
            area_m2=3.0,
            shade_required=True,
            shade_reason="High solar power detected",
            effective_threshold=100.0,
        )

        assert result.shade_required is True
        assert result.shade_reason == "High solar power detected"
        assert result.effective_threshold == 100.0

    @pytest.mark.parametrize(
        ("power_total", "power_direct", "power_diffuse", "expected_total"),
        [
            (100.0, 70.0, 30.0, 100.0),
            (0.0, 0.0, 0.0, 0.0),
            (50.5, 35.5, 15.0, 50.5),
        ],
    )
    def test_window_calculation_result_power_consistency(
        self,
        power_total: float,
        power_direct: float,
        power_diffuse: float,
        expected_total: float,
    ) -> None:
        """Test that power values are consistent."""
        result = WindowCalculationResult(
            power_total=power_total,
            power_direct=power_direct,
            power_diffuse=power_diffuse,
            power_direct_raw=power_direct,
            power_diffuse_raw=power_diffuse,
            power_total_raw=power_total,
            shadow_factor=1.0,
            is_visible=True,
            area_m2=1.0,
        )

        assert result.power_total == expected_total


class TestShadeRequestFlow:
    """Test cases for ShadeRequestFlow dataclass."""

    def test_shade_request_flow_creation(self) -> None:
        """Test basic creation of ShadeRequestFlow."""
        window_data = {"id": "window1", "area": 2.5}
        effective_config = {"threshold": 100.0, "enabled": True}
        external_states = {"temperature": 25.0, "humidity": 60.0}
        solar_result = WindowCalculationResult(
            power_total=120.0,
            power_direct=90.0,
            power_diffuse=30.0,
            power_direct_raw=95.0,
            power_diffuse_raw=35.0,
            power_total_raw=130.0,
            shadow_factor=0.85,
            is_visible=True,
            area_m2=2.5,
        )

        request = ShadeRequestFlow(
            window_data=window_data,
            effective_config=effective_config,
            external_states=external_states,
            scenario_b_enabled=True,
            scenario_c_enabled=False,
            solar_result=solar_result,
        )

        assert request.window_data == window_data
        assert request.effective_config == effective_config
        assert request.external_states == external_states
        assert request.scenario_b_enabled is True
        assert request.scenario_c_enabled is False
        assert request.solar_result == solar_result

    def test_shade_request_flow_with_minimal_data(self) -> None:
        """Test ShadeRequestFlow with minimal required data."""
        window_data = {}
        effective_config = {}
        external_states = {}
        solar_result = WindowCalculationResult(
            power_total=0.0,
            power_direct=0.0,
            power_diffuse=0.0,
            power_direct_raw=0.0,
            power_diffuse_raw=0.0,
            power_total_raw=0.0,
            shadow_factor=0.0,
            is_visible=False,
            area_m2=0.0,
        )

        request = ShadeRequestFlow(
            window_data=window_data,
            effective_config=effective_config,
            external_states=external_states,
            scenario_b_enabled=False,
            scenario_c_enabled=False,
            solar_result=solar_result,
        )

        assert request.window_data == {}
        assert request.effective_config == {}
        assert request.external_states == {}
        assert request.scenario_b_enabled is False
        assert request.scenario_c_enabled is False


class TestFlowIntegrationMixin:
    """Test cases for FlowIntegrationMixin class."""

    def test_placeholder_methods_raise_not_implemented(self) -> None:
        """Test that placeholder methods are now implemented and work correctly."""
        mixin = FlowIntegrationMixin()

        # Test _get_subentries_by_type - now implemented
        result = mixin._get_subentries_by_type("window")
        assert isinstance(result, dict)

        # Test get_effective_config_from_flows - now implemented
        result = mixin.get_effective_config_from_flows("window1")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], dict)
        assert isinstance(result[1], dict)

        # Test calculate_all_windows_from_flows - now implemented
        result = mixin.calculate_all_windows_from_flows()
        assert isinstance(result, dict)

    def test_get_window_config_from_flow_success(self) -> None:
        """Test successful window config retrieval."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method
        expected_config = {"area": 2.5, "orientation": "south", "threshold": 100.0}
        mixin._get_subentries_by_type = Mock(return_value={"window1": expected_config})

        result = mixin._get_window_config_from_flow("window1")

        assert result == expected_config
        mixin._get_subentries_by_type.assert_called_once_with("window")

    def test_get_window_config_from_flow_not_found(self) -> None:
        """Test window config retrieval when window not found."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method
        mixin._get_subentries_by_type = Mock(return_value={"window2": {"area": 3.0}})

        result = mixin._get_window_config_from_flow("window1")

        assert result == {}
        mixin._get_subentries_by_type.assert_called_once_with("window")

    def test_get_window_config_from_flow_exception_handling(self) -> None:
        """Test window config retrieval with exception handling."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method to raise exception
        mixin._get_subentries_by_type = Mock(side_effect=Exception("Test error"))

        result = mixin._get_window_config_from_flow("window1")

        assert result == {}
        mixin._get_subentries_by_type.assert_called_once_with("window")

    def test_get_group_config_from_flow_success(self) -> None:
        """Test successful group config retrieval."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method
        expected_config = {"windows": ["window1", "window2"], "threshold": 80.0}
        mixin._get_subentries_by_type = Mock(return_value={"group1": expected_config})

        result = mixin._get_group_config_from_flow("group1")

        assert result == expected_config
        mixin._get_subentries_by_type.assert_called_once_with("group")

    def test_get_group_config_from_flow_not_found(self) -> None:
        """Test group config retrieval when group not found."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method
        mixin._get_subentries_by_type = Mock(
            return_value={"group2": {"windows": ["window3"]}}
        )

        result = mixin._get_group_config_from_flow("group1")

        assert result == {}
        mixin._get_subentries_by_type.assert_called_once_with("group")

    def test_get_group_config_from_flow_exception_handling(self) -> None:
        """Test group config retrieval with exception handling."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method to raise exception
        mixin._get_subentries_by_type = Mock(side_effect=Exception("Test error"))

        result = mixin._get_group_config_from_flow("group1")

        assert result == {}
        mixin._get_subentries_by_type.assert_called_once_with("group")

    def test_get_global_config_from_flow_success_specific_global(self) -> None:
        """Test successful global config retrieval with specific global entry."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method
        expected_config = {"default_threshold": 50.0, "enabled": True}
        mixin._get_subentries_by_type = Mock(return_value={"global": expected_config})

        result = mixin._get_global_config_from_flow()

        assert result == expected_config
        mixin._get_subentries_by_type.assert_called_once_with("global")

    def test_get_global_config_from_flow_success_first_entry(self) -> None:
        """Test successful global config retrieval using first available entry."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method
        config1 = {"default_threshold": 50.0}
        config2 = {"default_threshold": 60.0}
        mixin._get_subentries_by_type = Mock(
            return_value={"entry1": config1, "entry2": config2}
        )

        result = mixin._get_global_config_from_flow()

        assert result == config1  # Should return first entry
        mixin._get_subentries_by_type.assert_called_once_with("global")

    def test_get_global_config_from_flow_empty_config(self) -> None:
        """Test global config retrieval when no config is available."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method
        mixin._get_subentries_by_type = Mock(return_value={})

        result = mixin._get_global_config_from_flow()

        assert result == {}
        mixin._get_subentries_by_type.assert_called_once_with("global")

    def test_get_global_config_from_flow_exception_handling(self) -> None:
        """Test global config retrieval with exception handling."""
        mixin = FlowIntegrationMixin()

        # Mock the _get_subentries_by_type method to raise exception
        mixin._get_subentries_by_type = Mock(side_effect=Exception("Test error"))

        result = mixin._get_global_config_from_flow()

        assert result == {}
        mixin._get_subentries_by_type.assert_called_once_with("global")
