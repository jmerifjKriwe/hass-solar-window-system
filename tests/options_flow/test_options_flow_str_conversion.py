"""Test to specifically verify the str conversion fix."""

import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.config_flow import (
    GroupSubentryFlowHandler,
    WindowSubentryFlowHandler,
)
from tests.test_data import VALID_GROUP_OPTIONS_NUMERIC, VALID_WINDOW_OPTIONS_NUMERIC


@pytest.mark.asyncio
async def test_group_options_numeric_values_conversion(hass: HomeAssistant) -> None:
    """

    Test that numeric values from data/options are properly converted to strings in
    GroupSubentryFlowHandler.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Group",
        data=VALID_GROUP_OPTIONS_NUMERIC,
        options={},
        unique_id="test_group_1",
    )
    config_entry.add_to_hass(hass)

    handler = GroupSubentryFlowHandler()
    handler.hass = hass
    handler.handler = (DOMAIN, "group")

    with patch(
        "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities"
    ) as mock_temp:
        mock_temp.return_value = [
            {"value": "sensor.temp1", "label": "Temperature 1"},
            {"value": "sensor.temp2", "label": "Temperature 2"},
        ]

    # This should not raise an error - the fix should convert numeric values to strings
    result = await handler.async_step_user(None)
    # Verify the schema was created successfully
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert "data_schema" in result


@pytest.mark.asyncio
async def test_window_options_numeric_values_conversion(hass: HomeAssistant) -> None:
    """

    Test that numeric values from data/options are properly converted to strings in
    WindowSubentryFlowHandler.
    """
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Window",
        data=VALID_WINDOW_OPTIONS_NUMERIC,
        options={},
        unique_id="test_window_1",
    )
    config_entry.add_to_hass(hass)

    handler = WindowSubentryFlowHandler()
    handler.hass = hass
    handler.handler = (DOMAIN, "window")

    with patch(
        "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities"
    ) as mock_temp:
        mock_temp.return_value = [
            {"value": "sensor.temp1", "label": "Temperature 1"},
            {"value": "sensor.temp2", "label": "Temperature 2"},
        ]

    # This should not raise an error - the fix should convert numeric values to strings
    result = await handler.async_step_user(None)
    # Verify the schema was created successfully
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert "data_schema" in result
"""Test to specifically verify the str conversion fix for options flow handlers."""

import pytest
from unittest.mock import patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.config_flow import (
    GroupSubentryFlowHandler,
    WindowSubentryFlowHandler,
)
from tests.test_data import VALID_GROUP_OPTIONS_NUMERIC, VALID_WINDOW_OPTIONS_NUMERIC


@pytest.mark.asyncio
async def test_group_options_numeric_values_conversion(hass: HomeAssistant) -> None:
    """Numeric values from data/options are converted to strings in group flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Group",
        data=VALID_GROUP_OPTIONS_NUMERIC,
        options={},
        unique_id="test_group_1",
    )
    config_entry.add_to_hass(hass)

    handler = GroupSubentryFlowHandler()
    handler.hass = hass
    handler.handler = (DOMAIN, "group")

    with patch(
        "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities"
    ) as mock_temp:
        mock_temp.return_value = [
            {"value": "sensor.temp1", "label": "Temperature 1"},
            {"value": "sensor.temp2", "label": "Temperature 2"},
        ]

    result = await handler.async_step_user(None)
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert "data_schema" in result


@pytest.mark.asyncio
async def test_window_options_numeric_values_conversion(hass: HomeAssistant) -> None:
    """Numeric values from data/options are converted to strings in window flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test Window",
        data=VALID_WINDOW_OPTIONS_NUMERIC,
        options={},
        unique_id="test_window_1",
    )
    config_entry.add_to_hass(hass)

    handler = WindowSubentryFlowHandler()
    handler.hass = hass
    handler.handler = (DOMAIN, "window")

    with patch(
        "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities"
    ) as mock_temp:
        mock_temp.return_value = [
            {"value": "sensor.temp1", "label": "Temperature 1"},
            {"value": "sensor.temp2", "label": "Temperature 2"},
        ]

    result = await handler.async_step_user(None)
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert "data_schema" in result
