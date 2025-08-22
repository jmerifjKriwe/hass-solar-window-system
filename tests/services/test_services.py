"""Test all registered services for Solar Window System integration."""

import pytest

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_recalculate_service_triggers_all(hass: HomeAssistant):
    """Test that the recalculate service triggers recalculation for all windows."""
    # Set up integration so service is registered
    entry = MockConfigEntry(domain=DOMAIN, data={"entry_type": "global_config"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    # Now call the service
    try:
        await hass.services.async_call(DOMAIN, "recalculate", {}, blocking=True)
    except Exception as e:
        raise AssertionError(f"Service call failed: {e}")


@pytest.mark.asyncio
async def test_recalculate_service_invalid_window(hass: HomeAssistant):
    """Test recalculate service with invalid window id (should not crash)."""
    # Set up integration so service is registered
    entry = MockConfigEntry(domain=DOMAIN, data={"entry_type": "global_config"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    # Now call the service with invalid window_id
    try:
        await hass.services.async_call(
            DOMAIN, "recalculate", {"window_id": "invalid"}, blocking=True
        )
    except Exception as e:
        raise AssertionError(f"Service call failed: {e}")
"""Tests for registered services of the Solar Window System integration."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_recalculate_service_triggers_all(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"entry_type": "global_config"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Call the service; ensure it does not raise
    try:
        await hass.services.async_call(DOMAIN, "recalculate", {}, blocking=True)
    except Exception as exc:
        raise AssertionError(f"Service call failed: {exc}")


@pytest.mark.asyncio
async def test_recalculate_service_invalid_window(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"entry_type": "global_config"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    try:
        await hass.services.async_call(
            DOMAIN, "recalculate", {"window_id": "invalid"}, blocking=True
        )
    except Exception as exc:
        raise AssertionError(f"Service call failed: {exc}")
"""Test all registered services for Solar Window System integration."""

import pytest

from unittest.mock import AsyncMock
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_recalculate_service_triggers_all(hass: HomeAssistant):
    """Test that the recalculate service triggers recalculation for all windows."""
    entry = MockConfigEntry(domain=DOMAIN, data={"entry_type": "global_config"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(DOMAIN, "recalculate", {}, blocking=True)


@pytest.mark.asyncio
async def test_recalculate_service_invalid_window(hass: HomeAssistant):
    """Test recalculate service with invalid window id (should not crash)."""
    entry = MockConfigEntry(domain=DOMAIN, data={"entry_type": "global_config"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, "recalculate", {"window_id": "invalid"}, blocking=True
    )
