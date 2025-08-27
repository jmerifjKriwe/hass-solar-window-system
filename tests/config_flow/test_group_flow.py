"""
Test group config flow.

Type annotations and docstrings in tests can be noisy; disable ANN001 and
D103 for this test module.
"""

# ruff: noqa: S101

from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.config_flow import GroupSubentryFlowHandler
from custom_components.solar_window_system.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from tests.test_data import VALID_GLOBAL_BASIC, VALID_GLOBAL_ENHANCED


def mock_group_parent_entry() -> MockConfigEntry:
    """Return a MockConfigEntry that represents a parent group entry."""
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


@pytest.fixture
def mock_global_config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry that represents a configured global entry."""
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
async def test_group_subentry_flow_add_and_invalid(
    hass: HomeAssistant,
    mock_global_config_entry: MockConfigEntry,
) -> None:
    """
    Verify adding a group subentry proceeds to enhanced step and
    invalid values error.
    """
    parent = mock_group_parent_entry()
    parent.add_to_hass(hass)
    mock_global_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities",
        return_value=[{"label": "Indoor Temp", "value": "sensor.indoor_temp"}],
    ):
        flow_handler = GroupSubentryFlowHandler()
        flow_handler.hass = hass
        flow_handler.handler = DOMAIN
        flow_handler.parent_entry_id = parent.entry_id

        user_input = {
            "name": "Test Group",
            "indoor_temperature_sensor": "sensor.indoor_temp",
            "diffuse_factor": "0.15",
            "threshold_direct": "200",
            "threshold_diffuse": "150",
            "temperature_indoor_base": "23.0",
            "temperature_outdoor_base": "19.5",
        }
        result = await flow_handler.async_step_user(user_input)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "enhanced"

        bad_input = {
            "name": "Test Group",
            "indoor_temperature_sensor": "sensor.indoor_temp",
            "diffuse_factor": "0.01",
            "threshold_direct": "200",
            "threshold_diffuse": "150",
            "temperature_indoor_base": "23.0",
            "temperature_outdoor_base": "19.5",
        }
        result2 = await flow_handler.async_step_user(bad_input)
        assert result2["type"] == FlowResultType.FORM
        errors = result2.get("errors")
        assert errors
        assert "diffuse_factor" in errors
