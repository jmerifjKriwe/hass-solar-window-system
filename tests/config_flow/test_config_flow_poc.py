"""
PoC tests for config flow refactor.

This file demonstrates the approach for testing config flows using the
Home Assistant test helpers and project fixtures.
"""

from __future__ import annotations

import importlib


def test_config_flow_imports_cleanly() -> None:
    """Ensure the config_flow module imports and exposes the expected class."""
    mod = importlib.import_module("custom_components.solar_window_system.config_flow")
    assert hasattr(mod, "SolarWindowSystemConfigFlow")
