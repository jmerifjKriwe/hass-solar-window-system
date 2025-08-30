"""
Unit tests for the SolarWindowCalculator core module.

This test suite provides comprehensive coverage for the main calculator class,
including initialization, entity state management, caching functionality,
and fallback logic.
"""

import logging
import time
from typing import Any
from unittest.mock import Mock, patch

import pytest

from custom_components.solar_window_system.calculator import SolarWindowCalculator
from custom_components.solar_window_system.modules.core import (
    SolarWindowCalculator as ModularSolarWindowCalculator,
)


class TestModularSolarWindowCalculator:
    """Test suite for the modular SolarWindowCalculator core functionality."""

    def test_modular_initialization_with_configs(self) -> None:
        """Test modular calculator initialization with various configurations."""
        mock_hass = Mock()

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        assert calculator.hass == mock_hass
        assert calculator._entity_cache == {}
        assert calculator._cache_timestamp is None
        assert calculator._cache_ttl == 30
        assert calculator._lru_cache == {}
        assert calculator._lru_max_size == 100

    def test_lru_cache_initialization(self) -> None:
        """Test LRU cache initialization."""
        mock_hass = Mock()
        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Check LRU cache attributes
        assert hasattr(calculator, "_lru_cache")
        assert hasattr(calculator, "_lru_max_size")
        assert calculator._lru_max_size == 100
        assert isinstance(calculator._lru_cache, dict)

    @pytest.mark.asyncio
    async def test_get_lru_cached_entity_state_async_first_call(self) -> None:
        """Test async LRU cache with first call."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        result = await calculator._get_lru_cached_entity_state_async("sensor.temp")

        assert result == "25.5"
        mock_hass.states.get.assert_called_once_with("sensor.temp")
        assert "sensor.temp" in calculator._lru_cache

    @pytest.mark.asyncio
    async def test_get_lru_cached_entity_state_async_from_cache(self) -> None:
        """Test async LRU cache returns cached value."""
        mock_hass = Mock()
        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Pre-populate cache
        current_time = time.time()
        calculator._lru_cache["sensor.temp"] = ("cached_value", current_time)

        result = await calculator._get_lru_cached_entity_state_async("sensor.temp")

        assert result == "cached_value"
        # Should not call hass.states.get since value is cached
        mock_hass.states.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_lru_cached_entity_state_async_expired_cache(self) -> None:
        """Test async LRU cache with expired entry."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "new_value"
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Pre-populate cache with expired timestamp
        expired_time = time.time() - 40  # Older than TTL (30 seconds)
        calculator._lru_cache["sensor.temp"] = ("old_value", expired_time)

        result = await calculator._get_lru_cached_entity_state_async("sensor.temp")

        assert result == "new_value"
        mock_hass.states.get.assert_called_once_with("sensor.temp")
        # Cache should be updated
        assert calculator._lru_cache["sensor.temp"][0] == "new_value"

    def test_get_lru_cached_entity_state_sync_first_call(self) -> None:
        """Test sync LRU cache with first call."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        result = calculator._get_lru_cached_entity_state("sensor.temp")

        assert result == "25.5"
        mock_hass.states.get.assert_called_once_with("sensor.temp")
        assert "sensor.temp" in calculator._lru_cache

    def test_get_lru_cached_entity_state_sync_from_cache(self) -> None:
        """Test sync LRU cache returns cached value."""
        mock_hass = Mock()
        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Pre-populate cache
        current_time = time.time()
        calculator._lru_cache["sensor.temp"] = ("cached_value", current_time)

        result = calculator._get_lru_cached_entity_state("sensor.temp")

        assert result == "cached_value"
        mock_hass.states.get.assert_not_called()

    def test_lru_cache_max_size_enforcement(self) -> None:
        """Test LRU cache enforces maximum size."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "value"
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)
        calculator._lru_max_size = 2  # Small cache for testing

        # Fill cache to max size
        calculator._get_lru_cached_entity_state("sensor1")
        calculator._get_lru_cached_entity_state("sensor2")

        # Add one more - should evict oldest
        calculator._get_lru_cached_entity_state("sensor3")

        # Cache should only have 2 entries
        assert len(calculator._lru_cache) == 2
        assert "sensor1" not in calculator._lru_cache  # Oldest should be evicted
        assert "sensor2" in calculator._lru_cache
        assert "sensor3" in calculator._lru_cache

    @pytest.mark.asyncio
    async def test_get_safe_attr_async_valid_entity(self) -> None:
        """Test async get_safe_attr with valid entity and attribute."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.unit_of_measurement = "°C"
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        result = await calculator.get_safe_attr_async(
            "sensor.temp", "unit_of_measurement", "N/A"
        )

        assert result == "°C"

    @pytest.mark.asyncio
    async def test_get_safe_attr_async_missing_attribute(self) -> None:
        """Test async get_safe_attr with missing attribute."""
        mock_hass = Mock()
        mock_state = Mock()
        # Mock state without the requested attribute
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        result = await calculator.get_safe_attr_async(
            "sensor.temp", "unit_of_measurement", "default"
        )

    @pytest.mark.asyncio
    async def test_get_safe_attr_async_none_entity(self) -> None:
        """Test async get_safe_attr with None entity."""
        mock_hass = Mock()
        mock_hass.states.get.return_value = None

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        result = await calculator.get_safe_attr_async(
            "sensor.nonexistent", "unit", "default"
        )

        assert result == "default"

    def test_get_cached_entity_state_smart_invalidation(self) -> None:
        """Test smart cache invalidation in _get_cached_entity_state."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Set old cache timestamp
        old_time = time.time() - 40  # Older than TTL
        calculator._cache_timestamp = old_time
        calculator._entity_cache["sensor.fresh"] = "fresh_value"
        calculator._entity_cache["sensor.expired"] = "expired_value"

        # Set LRU cache with one expired entry
        calculator._lru_cache["sensor.expired"] = ("expired_value", old_time - 10)
        calculator._lru_cache["sensor.fresh"] = ("fresh_value", time.time())

        result = calculator._get_cached_entity_state("sensor.expired")

        # Should get fresh value from hass
        assert result == "25.5"
        # Expired LRU entry should be removed
        assert "sensor.expired" not in calculator._lru_cache
        # Fresh LRU entry should remain
        assert "sensor.fresh" in calculator._lru_cache

    def test_resolve_entity_state_with_fallback_logic(self) -> None:
        """Test _resolve_entity_state_with_fallback method."""
        mock_hass = Mock()
        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Test with empty entity_id
        result = calculator._resolve_entity_state_with_fallback(
            "", "closed", {"open", "closed"}
        )
        assert result == "closed"

        # Test with valid state
        with patch.object(calculator, "_get_cached_entity_state", return_value="open"):
            result = calculator._resolve_entity_state_with_fallback(
                "cover.window", "closed", {"open", "closed"}
            )
            assert result == "open"

        # Test with invalid state
        with patch.object(
            calculator, "_get_cached_entity_state", return_value="unknown"
        ):
            result = calculator._resolve_entity_state_with_fallback(
                "cover.window", "closed", {"open", "closed"}
            )
            assert result == "closed"

    @pytest.mark.asyncio
    def test_delegation_calculate_window_solar_power(self) -> None:
        """Test calculate_window_solar_power_with_shadow delegation."""
        mock_hass = Mock()
        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Mock the hass states for the calculation
        mock_state = Mock()
        mock_state.state = "800"
        mock_hass.states.get.return_value = mock_state

        effective_config = {"test": "config"}
        window_data = {"name": "test_window", "azimuth": 180.0, "area": 2.0}
        states = {"solar_radiation": 1000, "sun_elevation": 45.0, "sun_azimuth": 180.0}

        result = calculator.calculate_window_solar_power_with_shadow(
            effective_config, window_data, states
        )

        # Should return a WindowCalculationResult
        assert hasattr(result, "power_total")
        assert hasattr(result, "power_direct")
        assert hasattr(result, "power_diffuse")
        assert hasattr(result, "shadow_factor")
        assert hasattr(result, "is_visible")
        assert hasattr(result, "area_m2")
        assert hasattr(result, "shade_required")
        assert hasattr(result, "shade_reason")

    def test_delegation_create_debug_data(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test create_debug_data delegation."""
        mock_hass = Mock()
        mock_hass.data = {}  # Mock hass.data as a dict
        mock_hass.config = Mock()
        mock_hass.config.config_dir = "/tmp"  # Mock config directory

        # Mock entity registry to avoid Home Assistant library errors
        mock_entity_reg = Mock()
        mock_entity_reg.entities = {}

        with patch(
            "custom_components.solar_window_system.modules.debug.er.async_get",
            return_value=mock_entity_reg,
        ):
            calculator = ModularSolarWindowCalculator(hass=mock_hass)

            # Mock the hass states and entity registry for debug data creation
            mock_state = Mock()
            mock_state.state = "25.5"
            mock_hass.states.get.return_value = mock_state
            mock_hass.states.all.return_value = [("sensor.temp", mock_state)]

            with caplog.at_level(logging.ERROR):
                result = calculator.create_debug_data("window1")

            # Should return a dict with debug information
            assert isinstance(result, dict)
            assert "window_id" in result
            assert "timestamp" in result

            assert result == "default"

    @pytest.mark.asyncio
    async def test_get_safe_attr_async_none_entity(self) -> None:
        """Test async get_safe_attr with None entity."""
        mock_hass = Mock()
        mock_hass.states.get.return_value = None

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        result = await calculator.get_safe_attr_async(
            "sensor.nonexistent", "unit", "default"
        )

        assert result == "default"

    def test_get_cached_entity_state_smart_invalidation(self) -> None:
        """Test smart cache invalidation in _get_cached_entity_state."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Set old cache timestamp
        old_time = time.time() - 40  # Older than TTL
        calculator._cache_timestamp = old_time
        calculator._entity_cache["sensor.fresh"] = "fresh_value"
        calculator._entity_cache["sensor.expired"] = "expired_value"
        # Set timestamps for cache entries
        calculator._entity_cache_timestamps["sensor.fresh"] = time.time()  # Fresh
        calculator._entity_cache_timestamps["sensor.expired"] = old_time - 10  # Expired
        calculator._lru_cache["sensor.fresh"] = ("fresh_value", time.time())

        result = calculator._get_cached_entity_state("sensor.expired")

        # Should get fresh value from hass
        assert result == "25.5"
        # Expired entry should be removed and replaced with fresh value
        assert calculator._entity_cache["sensor.expired"] == "25.5"
        # Fresh entry should remain unchanged
        assert calculator._entity_cache["sensor.fresh"] == "fresh_value"
        # Check that expired entry got a new timestamp
        assert calculator._entity_cache_timestamps["sensor.expired"] > old_time

    def test_resolve_entity_state_with_fallback_logic(self) -> None:
        """Test _resolve_entity_state_with_fallback method."""
        mock_hass = Mock()
        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Test with empty entity_id
        result = calculator._resolve_entity_state_with_fallback(
            "", "closed", {"open", "closed"}
        )
        assert result == "closed"

        # Test with valid state
        with patch.object(calculator, "_get_cached_entity_state", return_value="open"):
            result = calculator._resolve_entity_state_with_fallback(
                "cover.window", "closed", {"open", "closed"}
            )
            assert result == "open"

        # Test with invalid state
        with patch.object(
            calculator, "_get_cached_entity_state", return_value="unknown"
        ):
            result = calculator._resolve_entity_state_with_fallback(
                "cover.window", "closed", {"open", "closed"}
            )
            assert result == "closed"

    def test_delegation_calculate_window_solar_power(self) -> None:
        """Test calculate_window_solar_power_with_shadow delegation."""
        mock_hass = Mock()
        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        # Mock the hass states for the calculation
        mock_state = Mock()
        mock_state.state = "800"
        mock_hass.states.get.return_value = mock_state

        effective_config = {"test": "config"}
        window_data = {"name": "test_window", "azimuth": 180.0, "area": 2.0}
        states = {"solar_radiation": 1000, "sun_elevation": 45.0, "sun_azimuth": 180.0}

        result = calculator.calculate_window_solar_power_with_shadow(
            effective_config, window_data, states
        )

        # Should return a WindowCalculationResult
        assert hasattr(result, "power_total")
        assert hasattr(result, "power_direct")
        assert hasattr(result, "power_diffuse")
        assert hasattr(result, "shadow_factor")
        assert hasattr(result, "is_visible")
        assert hasattr(result, "area_m2")
        assert hasattr(result, "shade_required")
        assert hasattr(result, "shade_reason")

    def test_delegation_create_debug_data(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test create_debug_data delegation."""
        mock_hass = Mock()
        mock_hass.data = {}  # Mock hass.data as a dict
        mock_hass.config = Mock()
        mock_hass.config.config_dir = "/tmp"  # Mock config directory

        # Mock entity registry to avoid Home Assistant library errors
        mock_entity_reg = Mock()
        mock_entity_reg.entities = {}

        with patch(
            "custom_components.solar_window_system.modules.debug.er.async_get",
            return_value=mock_entity_reg,
        ):
            calculator = ModularSolarWindowCalculator(hass=mock_hass)

            # Mock the hass states and entity registry for debug data creation
            mock_state = Mock()
            mock_state.state = "25.5"
            mock_hass.states.get.return_value = mock_state
            mock_hass.states.all.return_value = [("sensor.temp", mock_state)]

            with caplog.at_level(logging.ERROR):
                result = calculator.create_debug_data("window1")

            # Should return a dict with debug information
            assert isinstance(result, dict)
            assert "window_id" in result
            assert "timestamp" in result

    def test_initialization_with_configs(self) -> None:
        """Test calculator initialization with various configurations."""
        mock_hass = Mock()

        defaults_config = {"default_temp": 20.0}
        groups_config = {"group1": {"windows": ["win1", "win2"]}}
        windows_config = {"win1": {"azimuth": 180.0}}

        calculator = SolarWindowCalculator(
            hass=mock_hass,
            defaults_config=defaults_config,
            groups_config=groups_config,
            windows_config=windows_config,
        )

        assert calculator.hass == mock_hass
        assert calculator.defaults == defaults_config
        assert calculator.groups == groups_config
        assert calculator.windows == windows_config
        assert calculator._entity_cache == {}
        assert calculator._cache_timestamp is None
        assert calculator._cache_ttl == 30
        assert calculator.global_entry is None

    def test_initialization_with_none_configs(self) -> None:
        """Test calculator initialization with None configurations."""
        mock_hass = Mock()

        calculator = SolarWindowCalculator(hass=mock_hass)

        assert calculator.hass == mock_hass
        assert calculator.defaults == {}
        assert calculator.groups == {}
        assert calculator.windows == {}
        assert calculator._entity_cache == {}
        assert calculator._cache_timestamp is None
        assert calculator._cache_ttl == 30
        assert calculator.global_entry is None

    def test_get_safe_state_valid_entity(self) -> None:
        """Test getting safe state from valid entity."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_hass.states.get.return_value = mock_state

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator.get_safe_state("sensor.temperature")
        assert result == "25.5"
        mock_hass.states.get.assert_called_once_with("sensor.temperature")

    def test_get_safe_state_unavailable_entity(self) -> None:
        """Test getting safe state from unavailable entity."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "unavailable"
        mock_hass.states.get.return_value = mock_state

        calculator = SolarWindowCalculator(hass=mock_hass)

        # The implementation treats "unavailable" as invalid and returns default
        result = calculator.get_safe_state("sensor.temperature", default=20.0)
        assert result == 20.0

    def test_get_safe_state_none_entity(self) -> None:
        """Test getting safe state when entity doesn't exist."""
        mock_hass = Mock()
        mock_hass.states.get.return_value = None

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator.get_safe_state("sensor.nonexistent", default=15.0)
        assert result == 15.0

    def test_get_safe_state_exception_handling(self) -> None:
        """Test getting safe state with exception handling."""
        mock_hass = Mock()
        mock_hass.states.get.side_effect = AttributeError("Test error")

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator.get_safe_state("sensor.temperature", default=-1)
        assert result == -1

    def test_get_safe_attr_valid_entity(self) -> None:
        """Test getting safe attribute from valid entity."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        # Configure the mock to return the expected value for the 'unit' attribute
        mock_state.attributes = {"unit": "°C"}
        mock_hass.states.get.return_value = mock_state

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator.get_safe_attr("sensor.temperature", "unit")
        assert result == "°C"

    def test_get_safe_attr_missing_attribute(self) -> None:
        """Test getting safe attribute when attribute doesn't exist."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_state.attributes = {"temperature": "25.5"}  # No 'unit' attribute
        mock_hass.states.get.return_value = mock_state

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator.get_safe_attr("sensor.temperature", "unit", default="N/A")
        assert result == "N/A"

    def test_get_safe_attr_none_entity(self) -> None:
        """Test getting safe attribute when entity doesn't exist."""
        mock_hass = Mock()
        mock_hass.states.get.return_value = None

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator.get_safe_attr("sensor.nonexistent", "unit", default=0)
        assert result == 0

    def test_get_safe_attr_exception_handling(self) -> None:
        """Test getting safe attribute with exception handling."""
        mock_hass = Mock()
        mock_hass.states.get.side_effect = KeyError("Test error")

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator.get_safe_attr("sensor.temperature", "unit", default=-999)
        assert result == -999

    def test_get_cached_entity_state_first_call(self) -> None:
        """Test cached entity state on first call."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_hass.states.get.return_value = mock_state

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator._get_cached_entity_state("sensor.temperature")
        assert result == "25.5"
        assert "sensor.temperature" in calculator._entity_cache
        assert calculator._cache_timestamp is not None

    def test_get_cached_entity_state_from_cache(self) -> None:
        """Test getting entity state from cache."""
        mock_hass = Mock()
        calculator = SolarWindowCalculator(hass=mock_hass)

        # Pre-populate cache
        calculator._entity_cache["sensor.temperature"] = "25.5"
        calculator._cache_timestamp = time.time()

        result = calculator._get_cached_entity_state("sensor.temperature")

        assert result == "25.5"
        # Should not call hass.states.get when cached
        mock_hass.states.get.assert_not_called()

    def test_get_cached_entity_state_cache_expiry(self) -> None:
        """Test cache expiry and refresh."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "26.0"
        mock_hass.states.get.return_value = mock_state

        calculator = SolarWindowCalculator(hass=mock_hass)

        # Set old timestamp (expired cache)
        calculator._cache_timestamp = time.time() - 31  # 31 seconds ago
        calculator._entity_cache["sensor.temperature"] = "25.5"

        result = calculator._get_cached_entity_state("sensor.temperature")

        assert result == "26.0"  # New value from hass
        assert calculator._entity_cache["sensor.temperature"] == "26.0"
        mock_hass.states.get.assert_called_once_with("sensor.temperature")

    def test_get_cached_entity_state_with_default(self) -> None:
        """Test cached entity state with default value."""
        mock_hass = Mock()
        mock_hass.states.get.return_value = None

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator._get_cached_entity_state(
            "sensor.missing", default_value=20.0
        )
        assert result == 20.0
        assert calculator._entity_cache["sensor.missing"] == 20.0

    def test_resolve_entity_state_with_fallback_valid_state(self) -> None:
        """Test entity state resolution with valid state."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "open"
        mock_hass.states.get.return_value = mock_state

        calculator = SolarWindowCalculator(hass=mock_hass)

        valid_states = {"open", "closed"}
        result = calculator._resolve_entity_state_with_fallback(
            "cover.window", "closed", valid_states
        )

        assert result == "open"

    def test_resolve_entity_state_with_fallback_invalid_state(self) -> None:
        """Test entity state resolution with invalid state."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "unknown"
        mock_hass.states.get.return_value = mock_state

        calculator = SolarWindowCalculator(hass=mock_hass)

        valid_states = {"open", "closed"}
        result = calculator._resolve_entity_state_with_fallback(
            "cover.window", "closed", valid_states
        )

        assert result == "closed"  # Fallback used

    @pytest.mark.parametrize(
        ("entity_id", "default", "expected"),
        [
            ("sensor.temp", 20.0, 20.0),  # Default used for None entity
            ("sensor.temp", "N/A", "N/A"),  # String default
            ("sensor.temp", 0, 0),  # Integer default
        ],
    )
    def test_get_safe_state_parametrized_defaults(
        self, entity_id: str, default: Any, expected: Any
    ) -> None:
        """Parametrized test for get_safe_state with different defaults."""
        mock_hass = Mock()
        mock_hass.states.get.return_value = None

        calculator = SolarWindowCalculator(hass=mock_hass)

        result = calculator.get_safe_state(entity_id, default)
        assert result == expected

    @pytest.mark.parametrize(
        ("cache_age", "expected_calls"),
        [
            (10, 0),  # Cache valid, no hass call
            (35, 1),  # Cache expired, hass called
        ],
    )
    def test_cache_expiry_parametrized(
        self, cache_age: int, expected_calls: int
    ) -> None:
        """Parametrized test for cache expiry behavior."""
        mock_hass = Mock()
        mock_state = Mock()
        mock_state.state = "25.5"
        mock_hass.states.get.return_value = mock_state

        calculator = SolarWindowCalculator(hass=mock_hass)

        # Set cache with specific age
        calculator._cache_timestamp = time.time() - cache_age
        calculator._entity_cache["sensor.temp"] = "cached_value"

        result = calculator._get_cached_entity_state("sensor.temp")

        assert mock_hass.states.get.call_count == expected_calls
        if expected_calls == 0:
            assert result == "cached_value"
        else:
            assert result == "25.5"
