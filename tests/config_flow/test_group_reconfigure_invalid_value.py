"""Test for invalid values in group reconfigure flow."""

from unittest.mock import AsyncMock, patch

from custom_components.solar_window_system import config_flow
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from tests.helpers.test_framework import ConfigFlowTestCase
from tests.test_data import VALID_GLOBAL_ENHANCED


class TestGroupReconfigureInvalidValue(ConfigFlowTestCase):
    """Test for invalid values in group reconfigure flow."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.stored_data = {
            CONF_NAME: "Test Group",
            **VALID_GLOBAL_ENHANCED,
            "diffuse_factor": 0.2,
            "threshold_direct": 600,
            "threshold_diffuse": 200,
            "temperature_indoor_base": 24.0,
            "temperature_outdoor_base": 20.0,
        }

    async def test_invalid_diffuse_factor(self, hass: HomeAssistant) -> None:
        """Ensure invalid diffuse_factor in reconfigure shows error and is not saved."""
        reconfig_flow = config_flow.GroupSubentryFlowHandler()
        reconfig_flow.hass = hass
        # Use the public reconfigure entrypoint
        mock_subentry = AsyncMock()
        mock_subentry.data = self.stored_data
        with (
            patch.object(
                reconfig_flow, "_get_reconfigure_subentry", return_value=mock_subentry
            ),
            patch(
                "custom_components.solar_window_system.helpers.get_temperature_sensor_entities",
                return_value=[],
            ),
        ):
            result = await reconfig_flow.async_step_reconfigure(None)
            if result["type"] != "form":
                msg = f"Expected form, got {result['type']}"
                raise AssertionError(msg)

            invalid_input = {
                CONF_NAME: "Test Group",
                "diffuse_factor": "1.5",  # Invalid: > 1.0
                "threshold_direct": "600",
                "threshold_diffuse": "200",
                "temperature_indoor_base": "24.0",
                "temperature_outdoor_base": "20.0",
            }
            result2 = await reconfig_flow.async_step_reconfigure(invalid_input)
            if result2["type"] != "form":
                msg = f"Expected form, got {result2['type']}"
                raise AssertionError(msg)
            if "diffuse_factor" not in result2.get("errors", {}):
                msg = "Expected 'diffuse_factor' in errors"
                raise AssertionError(msg)
