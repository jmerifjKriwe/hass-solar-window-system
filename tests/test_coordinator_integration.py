"""Test the new coordinator integration."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.solar_window_system.coordinator import (
    SolarWindowSystemCoordinator,
)
from custom_components.solar_window_system.calculator import SolarWindowCalculator


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)

    # Mock states and get method
    states_mock = MagicMock()
    hass.states = states_mock

    def mock_get_state(entity_id):
        state_values = {
            # Global entities
            "sensor.solar_window_power_direct": MagicMock(state="900"),
            "sensor.solar_window_power_diffuse": MagicMock(state="100"),
            "sensor.solar_window_solar_radiation_sensor": MagicMock(state="800"),
            "sensor.solar_window_outdoor_temperature_sensor": MagicMock(state="28"),
            "select.solar_window_scenario_a_enable": MagicMock(state="enable"),
            "select.solar_window_scenario_b_enable": MagicMock(state="enable"),
            "select.solar_window_scenario_c_enable": MagicMock(state="enable"),
            "number.solar_window_scenario_a_threshold": MagicMock(state="300"),
            "number.solar_window_scenario_b_threshold": MagicMock(state="250"),
            "number.solar_window_scenario_c_threshold": MagicMock(state="200"),
            "sensor.solar_window_weather_forecast_max_temp": MagicMock(state="32"),
            "binary_sensor.solar_window_weather_warning": MagicMock(state="off"),
            "switch.solar_window_maintenance_mode": MagicMock(state="off"),
            # Room temperature for windows
            "sensor.room_temp_living": MagicMock(state="24"),
            "sensor.room_temp_bedroom": MagicMock(state="22"),
        }
        return state_values.get(entity_id)

    states_mock.get.side_effect = mock_get_state
    return hass


@pytest.fixture
def mock_entry():
    """Mock ConfigEntry with window subentries."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.title = "Test Window Configs"
    entry.data = {"entry_type": "window_configs"}

    # Mock subentries
    entry.subentries = {
        "window_1": MagicMock(
            title="Living Room Window",
            subentry_type="window",
            data={"room_temperature_sensor": "sensor.room_temp_living"},
        ),
        "window_2": MagicMock(
            title="Bedroom Window",
            subentry_type="window",
            data={"room_temperature_sensor": "sensor.room_temp_bedroom"},
        ),
    }

    return entry


@pytest.mark.asyncio
async def test_coordinator_initialization(mock_hass, mock_entry):
    """Test that coordinator initializes correctly."""
    coordinator = SolarWindowSystemCoordinator(mock_hass, mock_entry)

    assert coordinator.hass == mock_hass
    assert coordinator.entry == mock_entry
    assert coordinator.calculator is not None
    assert isinstance(coordinator.calculator, SolarWindowCalculator)


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
@pytest.mark.asyncio
async def test_coordinator_update_data(mock_hass, mock_entry):
    """Test that coordinator fetches data correctly."""
    coordinator = SolarWindowSystemCoordinator(mock_hass, mock_entry)

    # Perform first update
    await coordinator.async_refresh()

    assert coordinator.data is not None
    assert "summary" in coordinator.data
    assert "windows" in coordinator.data

    # Check summary
    summary = coordinator.data["summary"]
    assert "total_power" in summary
    assert "window_count" in summary
    assert "shading_count" in summary
    assert "calculation_time" in summary


@pytest.mark.asyncio
async def test_coordinator_window_data_access(mock_hass, mock_entry):
    """Test that coordinator provides window-specific data access."""
    coordinator = SolarWindowSystemCoordinator(mock_hass, mock_entry)

    # Perform first update
    await coordinator.async_refresh()

    # Test window data access methods
    living_room_shading = coordinator.get_window_shading_status("Living Room Window")
    bedroom_shading = coordinator.get_window_shading_status("Bedroom Window")

    # These should be boolean values
    assert isinstance(living_room_shading, bool)
    assert isinstance(bedroom_shading, bool)

    # Test get_window_data method
    living_room_data = coordinator.get_window_data("Living Room Window")
    bedroom_data = coordinator.get_window_data("Bedroom Window")

    assert isinstance(living_room_data, dict)
    assert isinstance(bedroom_data, dict)


@pytest.mark.asyncio
async def test_coordinator_reconfigure(mock_hass, mock_entry):
    """Test that coordinator can be reconfigured."""
    coordinator = SolarWindowSystemCoordinator(mock_hass, mock_entry)

    # Perform first update
    await coordinator.async_refresh()
    initial_data = coordinator.data

    # Reconfigure
    await coordinator.async_reconfigure()

    # Data should be refreshed
    await coordinator.async_refresh()
    assert coordinator.data is not None

    # Calculator should still be available
    assert coordinator.calculator is not None


def test_coordinator_with_missing_calculator(mock_hass):
    """Test coordinator behavior when calculator fails to initialize."""
    # Create entry without subentries to trigger calculator initialization failure
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_id"
    entry.title = "Test Window Configs"
    entry.data = {"entry_type": "window_configs"}
    entry.subentries = None

    coordinator = SolarWindowSystemCoordinator(mock_hass, entry)

    # Calculator should be None if initialization fails
    # But coordinator should still be created
    assert coordinator.hass == mock_hass
    assert coordinator.entry == entry


@pytest.mark.asyncio
async def test_flow_based_calculation_called(mock_hass, mock_entry):
    """Test that the coordinator actually calls the new flow-based calculation."""
    coordinator = SolarWindowSystemCoordinator(mock_hass, mock_entry)

    # Mock the calculate_all_windows_from_flows method to verify it's called
    original_method = coordinator.calculator.calculate_all_windows_from_flows
    coordinator.calculator.calculate_all_windows_from_flows = MagicMock(
        return_value={
            "summary": {"total_power": 1000, "window_count": 2, "shading_count": 1},
            "windows": {
                "Living Room Window": {"requires_shading": True},
                "Bedroom Window": {"requires_shading": False},
            },
        }
    )

    # Perform update
    await coordinator.async_refresh()

    # Verify the flow-based method was called
    coordinator.calculator.calculate_all_windows_from_flows.assert_called_once()

    # Verify data is correct
    assert coordinator.data["summary"]["window_count"] == 2
    assert coordinator.get_window_shading_status("Living Room Window") is True
    assert coordinator.get_window_shading_status("Bedroom Window") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
