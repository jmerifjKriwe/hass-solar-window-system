"""
Parametrized platform tests PoC for Solar Window System.

This file demonstrates how platform tests can be consolidated and
parametrized to reduce duplication.
"""

from __future__ import annotations

import importlib

import pytest

from tests.helpers.fixtures_helpers import (
    collect_entities_for_setup,
    create_global_config_entry,
    ensure_global_device,
)

PLATFORMS: list[tuple[str, str]] = [
    ("number", "custom_components.solar_window_system.number"),
    ("text", "custom_components.solar_window_system.text"),
    ("select", "custom_components.solar_window_system.select"),
    ("switch", "custom_components.solar_window_system.switch"),
    ("sensor", "custom_components.solar_window_system.sensor"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(("platform_name", "module_path"), PLATFORMS)
async def test_platform_setup_minimal(hass, platform_name: str, module_path: str):
    """Minimal smoke test for platform setup using shared helpers."""
    entry = create_global_config_entry(hass, entry_id=f"test_{platform_name}_entry")
    ensure_global_device(hass, entry)

    module = importlib.import_module(module_path)
    added = await collect_entities_for_setup(hass, module, entry)

    # If the integration defines entities for this platform, ensure they expose unique_id
    if added:
        for entity in added:
            if not hasattr(entity, "_attr_unique_id"):
                raise AssertionError("Entity must expose unique_id attr")
