"""Lightweight smoke tests for the Solar Window System integration."""

from __future__ import annotations

import pytest

from homeassistant.helpers import device_registry as dr
from unittest.mock import AsyncMock
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.solar_window_system as integration
from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.asyncio
async def test_global_setup_smoke(hass, monkeypatch) -> None:
    """Smoke test: set up the global entry and ensure core wiring works."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global"},
        entry_id="smoke_global",
    )
    entry.add_to_hass(hass)

    # Avoid integration discovery in this smoke test
    monkeypatch.setattr(
        hass.config_entries,
        "async_forward_entry_setups",
        AsyncMock(return_value=None),
    )

    ok = await integration.async_setup_entry(hass, entry)
    assert ok is True

    # Device for global configuration should exist with canonical identifier
    device_registry = dr.async_get(hass)
    found = any(
        (DOMAIN, "global_config") in dev.identifiers
        for dev in device_registry.devices.values()
        if entry.entry_id in (dev.config_entries or set())
    )
    assert found

    # Service for creating subentry devices should be registered
    assert hass.services.has_service(DOMAIN, "create_subentry_devices")


@pytest.mark.asyncio
async def test_unload_smoke(hass, monkeypatch) -> None:
    """Smoke test: unload returns True for the global entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global"},
        entry_id="smoke_unload",
    )
    entry.add_to_hass(hass)

    # Avoid integration discovery in this smoke test
    monkeypatch.setattr(
        hass.config_entries,
        "async_forward_entry_setups",
        AsyncMock(return_value=None),
    )
    monkeypatch.setattr(
        hass.config_entries,
        "async_unload_platforms",
        AsyncMock(return_value=True),
    )

    await integration.async_setup_entry(hass, entry)
    ok = await integration.async_unload_entry(hass, entry)
    assert ok is True
