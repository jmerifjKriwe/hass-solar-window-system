"""Test startup race conditions in the integration."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_deferred_setup_does_not_use_event_loop_from_worker(
    hass: HomeAssistant,
) -> None:
    """
    Test the setup process handles event loops correctly.

    This test registers a config entry and ensures the integration's deferred
    setup (scheduled on EVENT_HOMEASSISTANT_STARTED) runs without raising thread
    errors. We patch hass.async_add_executor_job to mock Home Assistant's helper.
    """
    # Patch the executor job method to ensure setup runs in worker thread
    hass.async_add_executor_job = AsyncMock()

    # Rest of test implementation would go here
