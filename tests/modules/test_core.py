"""
Unit tests for the SolarWindowCalculator core module.

This test suite provides comprehensive coverage for the main calculator class,
including initialization, entity state management, caching functionality,
and fallback logic.
"""

import logging
import time
from unittest.mock import Mock, patch

import pytest

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
        # Create a real dict for attributes instead of relying on Mock behavior
        mock_state.attributes = {"unit_of_measurement": "°C"}
        mock_state.state = "available"  # Ensure state is not unknown/unavailable
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        result = await calculator.get_safe_attr_async(
            "sensor.temp", "unit_of_measurement", "N/A"
        )

        assert result == "°C"
        # Ensure the method was called correctly
        mock_hass.states.get.assert_called_with("sensor.temp")

    @pytest.mark.asyncio
    async def test_get_safe_attr_async_missing_attribute(self) -> None:
        """Test async get_safe_attr with missing attribute."""
        mock_hass = Mock()
        mock_state = Mock()
        # Mock state without the requested attribute
        mock_state.attributes = {}
        mock_hass.states.get.return_value = mock_state

        calculator = ModularSolarWindowCalculator(hass=mock_hass)

        result = await calculator.get_safe_attr_async(
            "sensor.temp", "unit_of_measurement", "default"
        )

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

    @pytest.mark.asyncio
    async def test_delegation_create_debug_data(
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
            "custom_components.solar_window_system.modules.debug.DebugMixin._get_entity_registry",
            return_value=mock_entity_reg,
        ):
            calculator = ModularSolarWindowCalculator(hass=mock_hass)

            # Mock the hass states and entity registry for debug data creation
            mock_state = Mock()
            mock_state.state = "25.5"
            mock_hass.states.get.return_value = mock_state
            mock_hass.states.all.return_value = [("sensor.temp", mock_state)]

            with caplog.at_level(logging.ERROR):
                result = await calculator.create_debug_data("window1")

            # Should return a dict with debug information
            assert isinstance(result, dict)
            assert "window_id" in result
            assert "timestamp" in result
