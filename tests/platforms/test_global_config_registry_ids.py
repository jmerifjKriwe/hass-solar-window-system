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
    assert hasattr(entity, "_attr_unique_id")
    assert entity._attr_unique_id == expected_unique_id

    expected_suggested_object_id = f"sws_global_{entity_key}"
    assert hasattr(entity, "_attr_suggested_object_id")
    assert entity._attr_suggested_object_id == expected_suggested_object_id

    expected_temp_name = f"SWS_GLOBAL {config['name']}"
    assert entity._attr_name == expected_temp_name
    assert hasattr(entity, "_entity_key")
    assert entity._entity_key == entity_key


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
        expected_unique_id = f"sws_global_{entity_key}"
        assert entity._attr_unique_id == expected_unique_id
