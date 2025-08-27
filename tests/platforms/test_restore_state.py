"""Test state restoration for Solar Window System entities after restart.

This module validates that RestoreEntity integration paths restore previous
state correctly for SWS sensors.
"""

# ruff: noqa: ANN001,D103,S101

from unittest.mock import Mock, patch

import pytest
from homeassistant.helpers.restore_state import RestoreEntity

from custom_components.solar_window_system.sensor import (
    SolarWindowSystemGroupDummySensor,
)


@pytest.mark.asyncio
async def test_restore_state_on_restart(hass) -> None:
    """Test that Solar Window System sensor restores its state after restart."""
    # Simulate a previous state
    old_state = Mock()
    old_state.state = 99
    old_state.attributes = {}

    # Patch RestoreEntity to return the old state
    with patch.object(RestoreEntity, "async_get_last_state", return_value=old_state):
        entity = SolarWindowSystemGroupDummySensor("group1", "Test Group")
        await entity.async_added_to_hass()
        assert entity.state == 99
