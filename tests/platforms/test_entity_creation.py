"""Tests for entity ID generation and global configuration entity creation."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.solar_window_system.const import (
    DOMAIN,
    ENTITY_PREFIX,
    GLOBAL_CONFIG_ENTITIES,
)


@pytest.mark.asyncio
class TestGlobalConfigEntityCreation:
    """Test automatic entity creation for global configuration."""

    async def test_entity_unique_ids_have_prefix(
        self, hass: HomeAssistant, expected_entity_unique_ids: dict[str, str]
    ) -> None:
        """Test that all entity unique IDs have the correct prefix."""
        for entity_key, expected_unique_id in expected_entity_unique_ids.items():
            assert expected_unique_id.startswith(ENTITY_PREFIX), (
                f"Entity {entity_key} unique_id should start with {ENTITY_PREFIX}"
            )
            assert expected_unique_id == f"{ENTITY_PREFIX}_global_{entity_key}", (
                f"Entity {entity_key} should have unique_id {ENTITY_PREFIX}_global_{entity_key}"
            )

    async def test_entity_id_generation_from_unique_id(
        self, hass: HomeAssistant, expected_entity_ids: dict[str, str]
    ) -> None:
        """Test that entity IDs are correctly generated from unique IDs."""
        for entity_key, expected_entity_id in expected_entity_ids.items():
            config = GLOBAL_CONFIG_ENTITIES[entity_key]
            platform = config["platform"]

            # Map platform types to actual platforms
            if platform == "input_number":
                platform = "number"
            elif platform == "input_text":
                platform = "text"
            elif platform == "input_select":
                platform = "select"
            elif platform == "input_boolean":
                platform = "switch"

            # The entity_id should be platform.unique_id_part
            # For unique_id "sws_global_window_g_value", entity_id should be
            # "number.sws_global_window_g_value"
            assert (
                expected_entity_id == f"{platform}.{ENTITY_PREFIX}_global_{entity_key}"
            )

    async def test_number_entities_creation(
        self,
        hass: HomeAssistant,
        entity_configs_by_platform: dict,
        global_config_entry: Mock,
    ) -> None:
        """Test that number entities are created correctly."""
        from custom_components.solar_window_system.number import async_setup_entry

        # Set up device registry with global config device
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=global_config_entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System Global Configuration",
            manufacturer="Solar Window System",
            model="Global Configuration",
        )

        # Track added entities
        added_entities = []

        def mock_async_add_entities(entities):
            added_entities.extend(entities)

        # Call the setup function
        await async_setup_entry(hass, global_config_entry, mock_async_add_entities)

        # Verify entities were created
        number_configs = entity_configs_by_platform["number"]
        assert len(added_entities) == len(number_configs)

        for i, (entity_key, config) in enumerate(number_configs):
            entity = added_entities[i]
            assert entity._attr_unique_id == f"{ENTITY_PREFIX}_global_{entity_key}"
            # Name is initially set with SWS_GLOBAL prefix; HA will adjust via registry later
            assert entity._attr_name.endswith(config["name"])  # prefix tolerated
            assert entity._attr_native_min_value == config["min"]
            assert entity._attr_native_max_value == config["max"]
            assert entity._attr_native_step == config["step"]

    async def test_text_entities_creation(
        self,
        hass: HomeAssistant,
        entity_configs_by_platform: dict,
        global_config_entry: Mock,
    ) -> None:
        """Test that text entities are created correctly."""
        from custom_components.solar_window_system.text import async_setup_entry

        # Set up device registry with global config device
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=global_config_entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System Global Configuration",
            manufacturer="Solar Window System",
            model="Global Configuration",
        )

        # Track added entities
        added_entities = []

        def mock_async_add_entities(entities):
            added_entities.extend(entities)

        # Call the setup function
        await async_setup_entry(hass, global_config_entry, mock_async_add_entities)

        # Verify entities were created
        text_configs = entity_configs_by_platform["text"]
        assert len(added_entities) == len(text_configs)

        for i, (entity_key, config) in enumerate(text_configs):
            entity = added_entities[i]
            assert entity._attr_unique_id == f"{ENTITY_PREFIX}_global_{entity_key}"
            assert entity._attr_name.endswith(config["name"])  # prefix tolerated
            assert entity._attr_native_max == config["max"]
            assert entity._attr_native_value == config["default"]

    async def test_select_entities_creation(
        self,
        hass: HomeAssistant,
        entity_configs_by_platform: dict,
        global_config_entry: Mock,
    ) -> None:
        """Test that select entities are created correctly."""
        from custom_components.solar_window_system.select import async_setup_entry

        # Set up device registry with global config device
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=global_config_entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System Global Configuration",
            manufacturer="Solar Window System",
            model="Global Configuration",
        )
        # Track added entities
        added_entities = []

        def mock_async_add_entities(entities):
            added_entities.extend(entities)

        # Call the setup function
        await async_setup_entry(hass, global_config_entry, mock_async_add_entities)

        # Verify entities were created
        select_configs = entity_configs_by_platform["select"]
        assert len(added_entities) == len(select_configs)

        for i, (entity_key, config) in enumerate(select_configs):
            entity = added_entities[i]
            assert entity._attr_unique_id == f"{ENTITY_PREFIX}_global_{entity_key}"
            assert entity._attr_name.endswith(config["name"])  # prefix tolerated
            # Options are dynamic; we ensure an empty placeholder is present as first option
            assert isinstance(entity._attr_options, list)
            assert entity._attr_options[0] == ""

    async def test_switch_entities_creation(
        self,
        hass: HomeAssistant,
        entity_configs_by_platform: dict,
        global_config_entry: Mock,
    ) -> None:
        """Test that switch entities are created correctly."""
        from custom_components.solar_window_system.switch import async_setup_entry

        # Set up device registry with global config device
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=global_config_entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System Global Configuration",
            manufacturer="Solar Window System",
            model="Global Configuration",
        )

        # Track added entities
        added_entities = []

        def mock_async_add_entities(entities):
            added_entities.extend(entities)

        # Call the setup function
        await async_setup_entry(hass, global_config_entry, mock_async_add_entities)

        # Verify entities were created
        switch_configs = entity_configs_by_platform["switch"]
        assert len(added_entities) == len(switch_configs)

        for i, (entity_key, config) in enumerate(switch_configs):
            entity = added_entities[i]
            assert entity._attr_unique_id == f"{ENTITY_PREFIX}_global_{entity_key}"
            assert entity._attr_name.endswith(config["name"])  # prefix tolerated
            assert entity._attr_is_on == config["default"]

    async def test_sensor_entities_creation(
        self,
        hass: HomeAssistant,
        entity_configs_by_platform: dict,
        global_config_entry: Mock,
    ) -> None:
        """Test that sensor entities are created correctly."""
        from custom_components.solar_window_system.sensor import async_setup_entry

        # Set up device registry with global config device
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=global_config_entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System Global Configuration",
            manufacturer="Solar Window System",
            model="Global Configuration",
        )

        # Track added entities
        added_entities = []

        def mock_async_add_entities(entities):
            added_entities.extend(entities)

        # Call the setup function
        await async_setup_entry(hass, global_config_entry, mock_async_add_entities)

        # Verify entities were created
        sensor_configs = entity_configs_by_platform["sensor"]
        assert len(added_entities) == len(sensor_configs)

        for i, (entity_key, config) in enumerate(sensor_configs):
            entity = added_entities[i]
            assert entity._attr_unique_id == f"{ENTITY_PREFIX}_global_{entity_key}"
            assert entity._attr_name.endswith(config["name"])  # prefix tolerated

    async def test_diagnostic_entities_have_correct_category(
        self, hass: HomeAssistant, debug_entities: list[str], global_config_entry: Mock
    ) -> None:
        """Test that debug entities have the diagnostic category."""
        from custom_components.solar_window_system.text import async_setup_entry

        # Set up device registry with global config device
        device_registry = dr.async_get(hass)
        device_registry.async_get_or_create(
            config_entry_id=global_config_entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System Global Configuration",
            manufacturer="Solar Window System",
            model="Global Configuration",
        )

        # Track added entities
        added_entities = []

        def mock_async_add_entities(entities):
            added_entities.extend(entities)

        # Call the setup function
        await async_setup_entry(hass, global_config_entry, mock_async_add_entities)

        # Find debug entities and verify their category
        debug_found = []
        for entity in added_entities:
            entity_key = entity._entity_key
            if entity_key in debug_entities:
                debug_found.append(entity_key)
                assert entity._attr_entity_category == EntityCategory.DIAGNOSTIC, (
                    f"Debug entity {entity_key} should have DIAGNOSTIC category"
                )

        # Ensure we found all debug entities
        assert set(debug_found) == set(debug_entities), (
            "Not all debug entities were found"
        )

    async def test_all_entities_have_device_info(
        self,
        hass: HomeAssistant,
        entity_configs_by_platform: dict,
        global_config_entry: Mock,
    ) -> None:
        """Test that all entities have proper device info."""
        from custom_components.solar_window_system.number import async_setup_entry

        # Set up device registry with global config device
        device_registry = dr.async_get(hass)
        expected_device = device_registry.async_get_or_create(
            config_entry_id=global_config_entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System Global Configuration",
            manufacturer="Solar Window System",
            model="Global Configuration",
        )

        # Track added entities
        added_entities = []

        def mock_async_add_entities(entities):
            added_entities.extend(entities)

        # Call the setup function
        await async_setup_entry(hass, global_config_entry, mock_async_add_entities)

        # Verify all entities have correct device info
        for entity in added_entities:
            device_info = entity._attr_device_info
            assert device_info is not None
            assert device_info["identifiers"] == expected_device.identifiers
            assert device_info["name"] == expected_device.name
            assert device_info["manufacturer"] == expected_device.manufacturer
            assert device_info["model"] == expected_device.model

    async def test_only_global_config_entry_processed(
        self, hass: HomeAssistant, window_config_entry: Mock
    ) -> None:
        """Test that only global configuration entries are processed."""
        from custom_components.solar_window_system.number import async_setup_entry

        # Track added entities
        added_entities = []

        def mock_async_add_entities(entities):
            added_entities.extend(entities)

        # Call setup with window entry (should not create entities)
        await async_setup_entry(hass, window_config_entry, mock_async_add_entities)

        # No entities should be created for window entries
        assert len(added_entities) == 0


@pytest.mark.asyncio
class TestEntityIdNamingConvention:
    """Test entity ID naming conventions and prefixing."""

    async def test_entity_prefix_constant(self) -> None:
        """Test that entity prefix constant is correctly defined."""
        assert ENTITY_PREFIX == "sws", (
            f"Entity prefix should be 'sws', got '{ENTITY_PREFIX}'"
        )

    async def test_unique_id_prefix_application(
        self, expected_entity_unique_ids: dict[str, str]
    ) -> None:
        """Test that unique IDs correctly apply the prefix."""
        for entity_key, unique_id in expected_entity_unique_ids.items():
            expected_prefix = f"{ENTITY_PREFIX}_global_"
            assert unique_id.startswith(expected_prefix), (
                f"Unique ID {unique_id} should start with {expected_prefix}"
            )

            # Verify the entity key is preserved
            assert unique_id.endswith(entity_key), (
                f"Unique ID {unique_id} should end with {entity_key}"
            )

    async def test_entity_id_format(self, expected_entity_ids: dict[str, str]) -> None:
        """Test that entity IDs follow the correct format."""
        for entity_key, entity_id in expected_entity_ids.items():
            # Entity ID should be platform.prefix_global_key
            parts = entity_id.split(".", 1)
            assert len(parts) == 2, (
                f"Entity ID {entity_id} should have format 'platform.name'"
            )

            platform, name_part = parts
            assert platform in [
                "number",
                "text",
                "select",
                "switch",
                "sensor",
            ], f"Platform {platform} is not recognized"

            expected_name = f"{ENTITY_PREFIX}_global_{entity_key}"
            assert name_part == expected_name, (
                f"Name part {name_part} should be {expected_name}"
            )

    async def test_entity_count_by_platform(
        self, entity_configs_by_platform: dict
    ) -> None:
        """Test that entities are correctly distributed across platforms."""
        # Verify we have entities for each platform
        total_entities = sum(
            len(configs) for configs in entity_configs_by_platform.values()
        )
        expected_total = len(GLOBAL_CONFIG_ENTITIES)

        assert total_entities == expected_total, (
            f"Total entities {total_entities} should equal {expected_total}"
        )

        # Verify each platform has at least one entity
        for platform, configs in entity_configs_by_platform.items():
            if len(configs) > 0:
                # Verify all entities in this platform have the correct platform mapping
                for entity_key, config in configs:
                    platform_mapping = {
                        "number": "input_number",
                        "text": "input_text",
                        "select": "input_select",
                        "switch": "input_boolean",
                        "sensor": "sensor",
                    }
                    expected_platform = platform_mapping[platform]
                    assert config["platform"] == expected_platform, (
                        f"Entity {entity_key} should have platform {expected_platform}"
                    )
