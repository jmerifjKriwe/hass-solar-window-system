"""Test for invalid values in reconfigure flow (Group)."""

import pytest
from unittest.mock import AsyncMock, patch
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from custom_components.solar_window_system import config_flow


@pytest.mark.asyncio
async def test_group_reconfigure_invalid_diffuse_factor(hass, global_config_entry):
    """
    Test that an invalid diffuse_factor in the reconfigure flow triggers an error and is not saved.
    """
    # Simulate stored valid data
    from tests.test_data import VALID_GLOBAL_BASIC, VALID_GLOBAL_ENHANCED

    stored_data = {
        CONF_NAME: "Test Group",
        **VALID_GLOBAL_ENHANCED,
        "diffuse_factor": 0.2,
        "threshold_direct": 600,
        "threshold_diffuse": 200,
        "temperature_indoor_base": 24.0,
        "temperature_outdoor_base": 20.0,
    }
    reconfig_flow = config_flow.GroupSubentryFlowHandler()
    reconfig_flow.hass = hass
    reconfig_flow.init_step = "user"
    mock_subentry = AsyncMock()
    mock_subentry.data = stored_data
    with (
        patch.object(
            reconfig_flow, "_get_reconfigure_subentry", return_value=mock_subentry
        ),
        patch(
            "custom_components.solar_window_system.helpers.get_temperature_sensor_entities",
            return_value=[],
        ),
    ):
        # Öffne das Formular über den Reconfigure-Flow
        result = await reconfig_flow.async_step_reconfigure(None)
        assert result["type"] == "form"
        # Versuche, einen ungültigen Wert zu speichern
        invalid_input = {
            CONF_NAME: "Test Group",
            "diffuse_factor": "1.5",  # Ungültig: > 1.0
            "threshold_direct": "600",
            "threshold_diffuse": "200",
            "temperature_indoor_base": "24.0",
            "temperature_outdoor_base": "20.0",
        }
        result2 = await reconfig_flow.async_step_reconfigure(invalid_input)
        assert result2["type"] == "form"
        assert "diffuse_factor" in result2.get("errors", {}), (
            f"Expected error for diffuse_factor, got: {result2.get('errors')}"
        )
