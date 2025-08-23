"""
Tests for the `recalculate` service of the Solar Window System integration.

Consolidated and parametrized to avoid duplication.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [{}, {"window_id": "invalid"}])
async def test_recalculate_service(hass: HomeAssistant, payload: dict) -> None:
    """
    Call the recalculate service with different payloads and ensure it doesn't raise.

    The test sets up the integration so the service is registered, then calls it with
    both an empty payload and an invalid window id to ensure the integration handles
    both cases without raising.
    """
    entry = MockConfigEntry(domain=DOMAIN, data={"entry_type": "global_config"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Service should be registered by the integration setup
    if not hass.services.has_service(DOMAIN, "recalculate"):
        msg = "recalculate service not registered"
        raise AssertionError(msg)

    # Call the service; if it raises, pytest will fail the test
    await hass.services.async_call(DOMAIN, "recalculate", payload, blocking=True)
