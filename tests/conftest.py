"""Global fixtures for Solar Window System integration tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

# Ensure custom_components is in sys.path for Home Assistant test discovery
sys.path.insert(0, str((Path(__file__).parent.parent).resolve()))

from custom_components.solar_window_system.const import (
    DOMAIN,
    GLOBAL_CONFIG_ENTITIES,
)


# Ensure custom integrations are enabled for all tests
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations defined in the test dir."""
    return


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Fixtures for Home Assistant test environment
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def mock_config_entry() -> Mock:
    """Return a mock config entry for global configuration."""
    return Mock(spec=ConfigEntry)


@pytest.fixture
def valid_global_input() -> dict[str, str]:
    """Return valid input for global configuration flow."""
    return {
        "entry_type": "global_config",
        "name": "Solar Window System",
    }


@pytest.fixture
def valid_window_input() -> dict[str, str | float | int]:
    """Return valid input for window configuration flow."""
    return {
        "window_id": "living_room_1",
        "name": "Living Room Window 1",
        "g_value": 0.75,
        "area": 2.5,
        "orientation": "south",
        "tilt_angle": 90,
    }


@pytest.fixture
def valid_group_input() -> dict[str, str]:
    """Return valid input for group configuration flow."""
    return {
        "entry_type": "group",
        "group": "test_group",
        "group_name": "Test Group",
    }


@pytest.fixture
def global_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a registered global config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={"entry_type": "global_config"},
        entry_id="global_config_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def window_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a registered window config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room Window 1",
        data={
            "window_id": "living_room_1",
            "name": "Living Room Window 1",
            "g_value": 0.75,
            "area": 2.5,
            "orientation": "south",
            "tilt_angle": 90,
        },
        entry_id="window_config_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def mock_device_registry() -> Mock:
    """Return a mock device registry."""
    registry = Mock(spec=dr.DeviceRegistry)

    # Mock global config device
    global_device = Mock(spec=dr.DeviceEntry)
    global_device.id = "global_device_id"
    global_device.identifiers = {(DOMAIN, "global_config")}
    global_device.name = "Solar Window System Global Configuration"
    global_device.manufacturer = "Solar Window System"
    global_device.model = "Global Configuration"
    global_device.config_entries = {"global_config_entry_id"}

    registry.devices = {"global_device_id": global_device}
    return registry


@pytest.fixture
def mock_entity_registry() -> Mock:
    """Return a mock entity registry."""
    registry = Mock(spec=er.EntityRegistry)
    registry.entities = {}
    return registry


@pytest.fixture
async def setup_global_config_device(
    hass: HomeAssistant, global_config_entry: Mock
) -> dr.DeviceEntry:
    """Set up a global configuration device in the device registry."""
    device_registry = dr.async_get(hass)

    return device_registry.async_get_or_create(
        config_entry_id=global_config_entry.entry_id,
        identifiers={(DOMAIN, "global_config")},
        name="Solar Window System Global Configuration",
        manufacturer="Solar Window System",
        model="Global Configuration",
    )


@pytest.fixture
def expected_entity_ids() -> dict[str, str]:
    """Return expected entity IDs for global configuration entities."""
    expected = {}
    for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
        platform = config["platform"]
        if platform == "input_number":
            platform = "number"
        elif platform == "input_text":
            platform = "text"
        elif platform == "input_select":
            platform = "select"
        elif platform == "input_boolean":
            platform = "switch"

        # Expected entity_id based on Home Assistant's automatic generation
        expected[entity_key] = f"{platform}.sws_global_{entity_key}"

    return expected


@pytest.fixture
def expected_entity_unique_ids() -> dict[str, str]:
    """Return expected unique IDs for global configuration entities."""
    expected = {}
    for entity_key in GLOBAL_CONFIG_ENTITIES:
        expected[entity_key] = f"sws_global_{entity_key}"

    return expected


@pytest.fixture
def entity_configs_by_platform() -> dict[str, list[tuple[str, dict[str, Any]]]]:
    """Return entity configurations grouped by platform."""
    platforms: dict[str, list[tuple[str, dict[str, Any]]]] = {
        "number": [],
        "text": [],
        "select": [],
        "switch": [],
        "sensor": [],
    }

    for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
        platform = config["platform"]
        if platform == "input_number":
            platforms["number"].append((entity_key, config))
        elif platform == "input_text":
            platforms["text"].append((entity_key, config))
        elif platform == "input_select":
            platforms["select"].append((entity_key, config))
        elif platform == "input_boolean":
            platforms["switch"].append((entity_key, config))
        elif platform == "sensor":
            platforms["sensor"].append((entity_key, config))

    return platforms


@pytest.fixture
def debug_entities() -> list[str]:
    """Return list of entity keys that should be diagnostic entities."""
    debug_entities = []
    for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
        if config.get("category") == "debug":
            debug_entities.append(entity_key)
    return debug_entities
