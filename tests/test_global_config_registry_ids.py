"""Global Configuration Registry Entity ID Tests."""

import pytest
from unittest.mock import Mock
from homeassistant.helpers import device_registry as dr
from custom_components.solar_window_system.number import GlobalConfigNumberEntity


@pytest.mark.asyncio
async def test_entity_attributes_have_sws_global_prefix():
    """Test that GlobalConfigNumberEntity correctly sets unique_id with sws_global_ prefix."""
    # Create test data
    entity_key = "window_g_value"
    
    # Mock config like in GLOBAL_CONFIG_ENTITIES
    config = {
        "name": "Window G-Value",
        "min": 0.1,
        "max": 1.0,
        "step": 0.01,
        "default": 0.5,
        "unit": None,
        "icon": "mdi:window-closed-variant",
    }
    
    # Mock device
    device = Mock(spec=dr.DeviceEntry)
    device.identifiers = {("solar_window_system", "global_config")}
    device.name = "Solar Window System Global Configuration"
    device.manufacturer = "Solar Window System"
    device.model = "Global Configuration"
    
    # Create entity
    entity = GlobalConfigNumberEntity(entity_key, config, device)
    
    # Check that unique_id is set with sws_global_ prefix
    expected_unique_id = f"sws_global_{entity_key}"
    assert hasattr(entity, "_attr_unique_id"), "Entity should have _attr_unique_id attribute"
    assert entity._attr_unique_id == expected_unique_id, (
        f"Expected unique_id '{expected_unique_id}', got '{entity._attr_unique_id}'"
    )
    
    # Check that suggested_object_id is set (used in our workaround)
    expected_suggested_object_id = f"sws_global_{entity_key}"
    assert hasattr(entity, "_attr_suggested_object_id"), "Entity should have _attr_suggested_object_id attribute"
    assert entity._attr_suggested_object_id == expected_suggested_object_id, (
        f"Expected suggested_object_id '{expected_suggested_object_id}', got '{entity._attr_suggested_object_id}'"
    )
    
    # Check that temporary name is set with prefix (for workaround)
    expected_temp_name = f"SWS_GLOBAL {config['name']}"
    assert entity._attr_name == expected_temp_name, (
        f"Expected temp name '{expected_temp_name}', got '{entity._attr_name}'"
    )
    
    # Check that entity_key is stored correctly
    assert hasattr(entity, "_entity_key"), "Entity should have _entity_key attribute"
    assert entity._entity_key == entity_key, (
        f"Expected entity_key '{entity_key}', got '{entity._entity_key}'"
    )


@pytest.mark.asyncio
async def test_multiple_entities_have_correct_prefixes():
    """Test that multiple entities all get correct sws_global_ prefixes."""
    # Create mock config and device for all tests
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
        
        # Each entity should have the correct prefixed unique_id
        expected_unique_id = f"sws_global_{entity_key}"
        assert entity._attr_unique_id == expected_unique_id, (
            f"Entity '{entity_key}' has incorrect unique_id: "
            f"expected '{expected_unique_id}', got '{entity._attr_unique_id}'"
        )
