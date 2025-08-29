"""Tests for refactored platform components."""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

from custom_components.solar_window_system.const import DOMAIN, ENTITY_PREFIX_GLOBAL
from custom_components.solar_window_system.global_config_entity import (
    GlobalConfigEntityBase,
    find_global_config_device,
    create_global_config_entities,
)


class TestGlobalConfigEntityBase:
    """Test the base class for global config entities."""

    @pytest.mark.asyncio
    async def test_base_entity_initialization(self) -> None:
        """Test that base entity initializes correctly."""
        device = Mock()
        device.identifiers = {(DOMAIN, "global_config")}
        device.name = "Test Device"
        device.manufacturer = "Test Manufacturer"
        device.model = "Test Model"

        config = {
            "name": "Test Entity",
            "icon": "mdi:test",
            "default": 42,
        }

        entity = GlobalConfigEntityBase("test_entity", config, device)

        assert entity._entity_key == "test_entity"
        assert entity._config == config
        assert entity._device == device
        assert entity._attr_unique_id == f"{ENTITY_PREFIX_GLOBAL}_test_entity"
        assert entity._attr_suggested_object_id == f"{ENTITY_PREFIX_GLOBAL}_test_entity"
        assert entity._attr_name == "SWS_GLOBAL Test Entity"
        assert entity._attr_has_entity_name is False
        assert entity._attr_icon == "mdi:test"
        assert entity._attr_device_info == {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
        }

    @pytest.mark.asyncio
    async def test_device_search_helper(self) -> None:
        """Test the device search helper function."""
        hass = Mock()
        device_registry = Mock()
        device = Mock()
        device.identifiers = {(DOMAIN, "global_config")}
        device.config_entries = {"test_entry"}
        device_registry.devices.values.return_value = [device]
        hass.data = {"device_registry": device_registry}

        # Mock the async_get function
        with patch(
            "homeassistant.helpers.device_registry.async_get",
            return_value=device_registry,
        ):
            result = find_global_config_device(hass, "test_entry")

        assert result == device

    @pytest.mark.asyncio
    async def test_device_search_helper_no_device(self) -> None:
        """Test the device search helper when no device is found."""
        hass = Mock()
        device_registry = Mock()
        device_registry.devices.values.return_value = []
        hass.data = {"device_registry": device_registry}

        with patch(
            "homeassistant.helpers.device_registry.async_get",
            return_value=device_registry,
        ):
            result = find_global_config_device(hass, "test_entry")

        assert result is None

    @pytest.mark.asyncio
    async def test_global_config_setup_helper(self) -> None:
        """Test the global config setup helper function."""
        device = Mock()
        device.identifiers = {(DOMAIN, "global_config")}

        # Mock entity class
        mock_entity_class = Mock()
        mock_entity_class.return_value = Mock()

        entities = create_global_config_entities(
            mock_entity_class, device, "input_number"
        )

        # Should create entities for input_number platform
        assert len(entities) > 0
        mock_entity_class.assert_called()


class TestRefactoredPlatforms:
    """Test that refactored platforms maintain functionality."""

    @pytest.mark.asyncio
    async def test_number_platform_refactored(self) -> None:
        """Test that number platform works after refactoring."""
        from custom_components.solar_window_system.number import (
            async_setup_entry,
            GlobalConfigNumberEntity,
        )
        from unittest.mock import AsyncMock

        # Mock hass and entry
        hass = Mock()
        entry = Mock()
        entry.title = "Solar Window System"
        entry.entry_id = "test_entry"

        # Mock device registry and device
        device_registry = Mock()
        device = Mock()
        device.identifiers = {(DOMAIN, "global_config")}
        device.config_entries = {"test_entry"}
        device.name = "Test Device"
        device.manufacturer = "Test Manufacturer"
        device.model = "Test Model"
        device_registry.devices.values.return_value = [device]

        # Mock async_add_entities
        async_add_entities = AsyncMock()

        with patch(
            "custom_components.solar_window_system.global_config_entity.dr.async_get",
            return_value=device_registry,
        ):
            await async_setup_entry(hass, entry, async_add_entities)

        # Verify that entities were added
        assert async_add_entities.called
        call_args = async_add_entities.call_args[0][0]
        assert len(call_args) > 0

        # Verify first entity is of correct type
        entity = call_args[0]
        assert isinstance(entity, GlobalConfigNumberEntity)

    @pytest.mark.asyncio
    async def test_select_platform_refactored(self) -> None:
        """Test that select platform works after refactoring."""
        from custom_components.solar_window_system.select import (
            async_setup_entry,
            GlobalConfigSelectEntity,
        )
        from unittest.mock import AsyncMock

        # Mock hass and entry
        hass = Mock()
        entry = Mock()
        entry.title = "Solar Window System"
        entry.entry_id = "test_entry"
        entry.data = {}

        # Mock device registry and device
        device_registry = Mock()
        device = Mock()
        device.identifiers = {(DOMAIN, "global_config")}
        device.config_entries = {"test_entry"}
        device.name = "Test Device"
        device.manufacturer = "Test Manufacturer"
        device.model = "Test Model"
        device_registry.devices.values.return_value = [device]

        # Mock async_add_entities
        async_add_entities = AsyncMock()

        with (
            patch(
                "custom_components.solar_window_system.global_config_entity.dr.async_get",
                return_value=device_registry,
            ),
            patch(
                "custom_components.solar_window_system.select._get_binary_sensor_entities",
                return_value=[],
            ),
            patch(
                "custom_components.solar_window_system.select._get_input_boolean_entities",
                return_value=[],
            ),
            patch(
                "custom_components.solar_window_system.select._get_temperature_sensor_entities",
                return_value=[],
            ),
        ):
            await async_setup_entry(hass, entry, async_add_entities)

        # Verify that entities were added
        assert async_add_entities.called
        call_args = async_add_entities.call_args[0][0]
        assert len(call_args) > 0

        # Verify first entity is of correct type
        entity = call_args[0]
        assert isinstance(entity, GlobalConfigSelectEntity)

    @pytest.mark.asyncio
    async def test_switch_platform_refactored(self) -> None:
        """Test that switch platform works after refactoring."""
        from custom_components.solar_window_system.switch import (
            async_setup_entry,
            GlobalConfigSwitchEntity,
        )
        from unittest.mock import AsyncMock

        # Mock hass and entry
        hass = Mock()
        entry = Mock()
        entry.title = "Solar Window System"
        entry.entry_id = "test_entry"

        # Mock device registry and device
        device_registry = Mock()
        device = Mock()
        device.identifiers = {(DOMAIN, "global_config")}
        device.config_entries = {"test_entry"}
        device.name = "Test Device"
        device.manufacturer = "Test Manufacturer"
        device.model = "Test Model"
        device_registry.devices.values.return_value = [device]

        # Mock async_add_entities
        async_add_entities = AsyncMock()

        with patch(
            "custom_components.solar_window_system.global_config_entity.dr.async_get",
            return_value=device_registry,
        ):
            await async_setup_entry(hass, entry, async_add_entities)

        # Verify that entities were added
        assert async_add_entities.called
        call_args = async_add_entities.call_args[0][0]
        assert len(call_args) > 0

        # Verify first entity is of correct type
        entity = call_args[0]
        assert isinstance(entity, GlobalConfigSwitchEntity)

    @pytest.mark.asyncio
    async def test_text_platform_refactored(self) -> None:
        """Test that text platform works after refactoring."""
        from custom_components.solar_window_system.text import (
            async_setup_entry,
            GlobalConfigTextEntity,
        )
        from unittest.mock import AsyncMock

        # Mock hass and entry
        hass = Mock()
        entry = Mock()
        entry.title = "Solar Window System"
        entry.entry_id = "test_entry"

        # Mock device registry and device
        device_registry = Mock()
        device = Mock()
        device.identifiers = {(DOMAIN, "global_config")}
        device.config_entries = {"test_entry"}
        device.name = "Test Device"
        device.manufacturer = "Test Manufacturer"
        device.model = "Test Model"
        device_registry.devices.values.return_value = [device]

        # Mock async_add_entities
        async_add_entities = AsyncMock()

        with patch(
            "custom_components.solar_window_system.global_config_entity.dr.async_get",
            return_value=device_registry,
        ):
            await async_setup_entry(hass, entry, async_add_entities)

        # Verify that entities were added
        assert async_add_entities.called
        call_args = async_add_entities.call_args[0][0]
        assert len(call_args) > 0

        # Verify first entity is of correct type
        entity = call_args[0]
        assert isinstance(entity, GlobalConfigTextEntity)

    @pytest.mark.asyncio
    async def test_sensor_platform_refactored(self) -> None:
        """Test that sensor platform works after refactoring."""
        from custom_components.solar_window_system.sensor import (
            async_setup_entry,
        )
        from custom_components.solar_window_system.global_config import (
            GlobalConfigSensor,
        )
        from unittest.mock import AsyncMock

        # Mock hass and entry
        hass = Mock()
        entry = Mock()
        entry.title = "Solar Window System"
        entry.entry_id = "test_entry"
        entry.data = {}

        # Mock device registry and device
        device_registry = Mock()
        device = Mock()
        device.identifiers = {(DOMAIN, "global_config")}
        device.config_entries = {"test_entry"}
        device.name = "Test Device"
        device.manufacturer = "Test Manufacturer"
        device.model = "Test Model"
        device_registry.devices.values.return_value = [device]

        # Mock async_add_entities
        async_add_entities = AsyncMock()

        with patch(
            "custom_components.solar_window_system.global_config_entity.dr.async_get",
            return_value=device_registry,
        ):
            await async_setup_entry(hass, entry, async_add_entities)

        # Verify that entities were added
        assert async_add_entities.called
        call_args = async_add_entities.call_args[0][0]
        assert len(call_args) > 0

        # Verify first entity is of correct type
        entity = call_args[0]
        assert isinstance(entity, GlobalConfigSensor)
