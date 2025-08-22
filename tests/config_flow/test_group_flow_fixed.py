"""Migrated test: group flow fixed scenarios."""

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from custom_components.solar_window_system.config_flow import GroupSubentryFlowHandler
from tests.test_data import VALID_GLOBAL_BASIC, VALID_GLOBAL_ENHANCED


def mock_group_parent_entry() -> MockConfigEntry:
    return MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Group configurations",
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        source="internal",
        entry_id="test_group_parent_id",
        unique_id=None,
    )


def mock_global_config_entry() -> MockConfigEntry:
    data = {"entry_type": "global_config"}
    data.update(VALID_GLOBAL_BASIC)
    data.update(VALID_GLOBAL_ENHANCED)
    return MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Solar Window System",
        data=data,
        source="user",
        entry_id="test_global_config_id",
        unique_id=None,
    )


@pytest.mark.asyncio
async def test_group_flow_basic_to_enhanced(hass: HomeAssistant) -> None:
    parent = mock_group_parent_entry()
    global_entry = mock_global_config_entry()
    parent.add_to_hass(hass)
    global_entry.add_to_hass(hass)

    with patch(
        "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities",
        return_value=[{"label": "Indoor Temp", "value": "sensor.indoor_temp"}],
    ):
        flow = GroupSubentryFlowHandler()
        flow.hass = hass
        try:
            flow.handler = DOMAIN
        except Exception:
            setattr(flow, "handler", DOMAIN)
        try:
            flow.parent_entry_id = parent.entry_id
        except Exception:
            setattr(flow, "parent_entry_id", parent.entry_id)

        user_input = {
            "name": "Group A",
            "indoor_temperature_sensor": "sensor.indoor_temp",
            "diffuse_factor": "0.2",
            "threshold_direct": "300",
            "threshold_diffuse": "200",
            "temperature_indoor_base": "22.0",
            "temperature_outdoor_base": "18.0",
        }
        result = await flow.async_step_user(user_input)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "enhanced"
