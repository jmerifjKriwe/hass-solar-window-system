"""Basic import test for the config_flow module."""

from __future__ import annotations

import importlib


def test_config_flow_imports_cleanly() -> None:
    """Ensure the config_flow module imports without syntax errors."""
    importlib.invalidate_caches()
    mod = importlib.import_module("custom_components.solar_window_system.config_flow")
    if not hasattr(mod, "SolarWindowSystemConfigFlow"):
        msg = "Missing SolarWindowSystemConfigFlow"
        raise AssertionError(msg)
