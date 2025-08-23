"""
Minimal integration-level tests for setup.

This file was migrated from tests/old/test_integration_setup.py which was empty
in the legacy copy. Create a minimal smoke test that ensures the integration
module can be imported and the domain constant exists.
"""

from custom_components.solar_window_system.const import DOMAIN


def test_integration_setup_importable() -> None:
    assert DOMAIN == "solar_window_system"
