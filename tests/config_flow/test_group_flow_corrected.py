"""Minimal tests for GroupSubentryFlowHandler (clean copy).

This file provides a small set of sanity tests to ensure the flow can be
imported and basic steps return forms. It is intentionally minimal so it
can be migrated safely and expanded later.
"""

import pytest
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.config_flow import GroupSubentryFlowHandler


@pytest.fixture
def mock_group_parent_entry() -> MockConfigEntry:
    return MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Group configurations",
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        source="internal",
        entry_id="test_group_parent_id",
    )


@pytest.fixture
def mock_global_config_entry() -> MockConfigEntry:
    data = {"entry_type": "global_config", "window_width": 1.0}
    return MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Solar Window System",
        data=data,
        source="user",
        entry_id="test_global_config_id",
    )


@pytest.mark.asyncio
async def test_group_subentry_flow_basic_step(hass: HomeAssistant, mock_group_parent_entry: MockConfigEntry, mock_global_config_entry: MockConfigEntry) -> None:
    """Test that the user step returns a form for the subentry flow."""
    mock_group_parent_entry.add_to_hass(hass)
    mock_global_config_entry.add_to_hass(hass)

    with patch("custom_components.solar_window_system.config_flow.get_temperature_sensor_entities", return_value=[{"label": "Indoor Temp", "value": "sensor.indoor_temp"}, {"label": "Inherit from Global", "value": "-1"}]):
        flow = GroupSubentryFlowHandler()
        flow.hass = hass
        try:
            flow.handler = DOMAIN
        except Exception:
            setattr(flow, "handler", DOMAIN)
        try:
            flow.parent_entry_id = mock_group_parent_entry.entry_id
        except Exception:
            setattr(flow, "parent_entry_id", mock_group_parent_entry.entry_id)

        result = await flow.async_step_user()
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_group_subentry_flow_complete(hass: HomeAssistant, mock_group_parent_entry: MockConfigEntry, mock_global_config_entry: MockConfigEntry) -> None:
    """Test a full create path that ends in CREATE_ENTRY (mocked)."""
    mock_group_parent_entry.add_to_hass(hass)
    mock_global_config_entry.add_to_hass(hass)

    with patch("custom_components.solar_window_system.config_flow.get_temperature_sensor_entities", return_value=[{"label": "Indoor Temp", "value": "sensor.indoor_temp"}]), patch("custom_components.solar_window_system.config_flow.GroupSubentryFlowHandler.async_create_entry") as mock_create_entry:
        mock_create_entry.return_value = {"type": FlowResultType.CREATE_ENTRY, "title": "Test Group", "data": {"name": "Test Group"}}

        flow = GroupSubentryFlowHandler()
        flow.hass = hass
        try:
            flow.handler = DOMAIN
        except Exception:
            setattr(flow, "handler", DOMAIN)
        try:
            flow.parent_entry_id = mock_group_parent_entry.entry_id
        except Exception:
            setattr(flow, "parent_entry_id", mock_group_parent_entry.entry_id)

        res1 = await flow.async_step_user({"name": "Test Group", "indoor_temperature_sensor": "sensor.indoor_temp"})
        assert res1["step_id"] == "enhanced"

        res2 = await flow.async_step_enhanced({})
        assert res2["type"] == FlowResultType.CREATE_ENTRY
        mock_create_entry.assert_called_once()
