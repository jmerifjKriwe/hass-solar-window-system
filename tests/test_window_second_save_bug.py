"""Test Window Options for the 'expected str' error on second save."""

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import VALID_GLOBAL_BASIC, VALID_GLOBAL_ENHANCED


from unittest.mock import patch
from homeassistant.data_entry_flow import FlowResultType
from custom_components.solar_window_system.config_flow import WindowSubentryFlowHandler


@pytest.mark.asyncio
async def test_window_options_second_save_expected_str_error(
    hass: HomeAssistant,
) -> None:
    """
    Test window subentry reconfigure (second save) scenario for 'expected str' error using WindowSubentryFlowHandler.
    """
    # Setup parent and global config entries
    parent_entry = MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Window configurations",
        data={
            "entry_type": "window_configs",
            "is_subentry_parent": True,
        },
        source="internal",
        entry_id="test_window_parent_id",
        unique_id=None,
    )
    data = {"entry_type": "global_config"}
    data.update(VALID_GLOBAL_BASIC)
    data.update(VALID_GLOBAL_ENHANCED)
    global_entry = MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Solar Window System",
        data=data,
        source="user",
        entry_id="test_global_config_id",
        unique_id=None,
    )
    parent_entry.add_to_hass(hass)
    global_entry.add_to_hass(hass)

    with patch(
        "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities",
        return_value=[{"label": "Room", "value": "sensor.temp_room"}],
    ):
        # Step 1: Create window subentry (first save)
        flow_handler = WindowSubentryFlowHandler()
        flow_handler.hass = hass

        user_input = {
            "name": "test_window",
            "indoor_temperature_sensor": "sensor.temp_room",
            "g_value": "0.6",
            "frame_width": "0.15",
            "tilt": "85",
            "diffuse_factor": "0.2",
            "threshold_direct": "250",
            "threshold_diffuse": "175",
            "temperature_indoor_base": "24.0",
            "temperature_outdoor_base": "18.5",
        }
    # First save (creation)
    result = await flow_handler.async_step_user(user_input)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "overrides"

    # Second save (reconfigure)
    result2 = await flow_handler.async_step_reconfigure(user_input)
    assert result2["type"] == FlowResultType.FORM
    assert result2["step_id"] == "overrides"
    # If we get here, the bug is fixed (no 'expected str' error)
