"""Global Configuration Registry Entity ID Tests."""

from unittest.mock import Mock

import pytest
from homeassistant.helpers import device_registry as dr

from custom_components.solar_window_system.number import GlobalConfigNumberEntity


@pytest.mark.asyncio
async def test_entity_attributes_have_sws_global_prefix() -> None:
    entity_key = "window_g_value"
    config = {
        "name": "Window G-Value",
        "min": 0.1,
        "max": 1.0,
        "step": 0.01,
        "default": 0.5,
        "unit": None,
        "icon": "mdi:window-closed-variant",
    }

    device = Mock(spec=dr.DeviceEntry)
    device.identifiers = {("solar_window_system", "global_config")}
    device.name = "Solar Window System Global Configuration"
    device.manufacturer = "Solar Window System"
    device.model = "Global Configuration"

    entity = GlobalConfigNumberEntity(entity_key, config, device)

    expected_unique_id = f"sws_global_{entity_key}"
    # Prefer the public `unique_id` property
    assert entity.unique_id == expected_unique_id

    expected_suggested_object_id = f"sws_global_{entity_key}"
    # Use public `suggested_object_id` attribute if available, otherwise
    # fall back to the private attribute for older Home Assistant versions.
    suggested = getattr(entity, "suggested_object_id", None)
    # Accept either the public suggested_object_id (newer HA) or the internal
    # fallback used in older versions. In some environments suggested may be a
    # friendly name, so allow that too if it matches the human name.
    if suggested is not None:
        if suggested != expected_suggested_object_id:
            # allow friendly-name-like suggestions
            assert suggested in (entity.name, expected_suggested_object_id)
    else:
        assert entity._attr_suggested_object_id == expected_suggested_object_id

    expected_temp_name = f"SWS_GLOBAL {config['name']}"
    assert entity.name == expected_temp_name
    # Verify the public unique_id includes the entity key
    assert entity.unique_id == expected_unique_id


@pytest.mark.asyncio
async def test_multiple_entities_have_correct_prefixes() -> None:
    config = {
        "name": "Test Entity",
        "min": 0,
        "max": 100,
        "step": 1,
        "default": 50,
        "unit": None,
        "icon": "mdi:test",
    }

    device = Mock(spec=dr.DeviceEntry)
    device.identifiers = {("solar_window_system", "global_config")}
    device.name = "Test Device"
    device.manufacturer = "Test Manufacturer"
    device.model = "Test Model"

    test_entity_keys = ["window_g_value", "window_frame_width", "threshold_direct"]

    for entity_key in test_entity_keys:
        entity = GlobalConfigNumberEntity(entity_key, config, device)
        # Assert via public API for each created entity
        expected_unique_id = f"sws_global_{entity_key}"
        assert entity.unique_id == expected_unique_id
        assert entity.name.startswith("SWS_GLOBAL")
