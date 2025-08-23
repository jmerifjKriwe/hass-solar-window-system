"""Ensure config_flow module imports cleanly and exposes the main flow class."""

import importlib


def test_config_flow_imports_cleanly() -> None:
    """Ensure the config_flow module imports and contains SolarWindowSystemConfigFlow."""
    importlib.invalidate_caches()
    mod = importlib.import_module("custom_components.solar_window_system.config_flow")
    assert hasattr(mod, "SolarWindowSystemConfigFlow"), (
        "Missing SolarWindowSystemConfigFlow"
    )
