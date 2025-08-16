"""Test for clean import and presence of main config flow class."""

import importlib
import pytest


def test_config_flow_imports_cleanly():
    """Ensure the config_flow module imports and contains SolarWindowSystemConfigFlow."""
    importlib.invalidate_caches()
    mod = importlib.import_module("custom_components.solar_window_system.config_flow")
    assert hasattr(mod, "SolarWindowSystemConfigFlow"), (
        "Missing SolarWindowSystemConfigFlow"
    )
