"""Test the Select platform setup for Solar Window System integration."""

from collections.abc import Iterable

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN, GLOBAL_CONFIG_ENTITIES
from custom_components.solar_window_system.select import async_setup_entry


"""Consolidated into `tests/platforms/test_platforms.py`."""

import pytest

pytest.skip(
    "Consolidated in tests/platforms/test_platforms.py",
    allow_module_level=True,
)
