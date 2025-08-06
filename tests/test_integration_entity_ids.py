"""Tests for Solar Window System entity ID integration."""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr, entity_registry as er
from tests.common import MockConfigEntry

from custom_components.solar_window_system.const import (
    DOMAIN,
    ENTITY_PREFIX,
    GLOBAL_CONFIG_ENTITIES,
)
from custom_components.solar_window_system.number import async_setup_entry


class TestEntityIDIntegration:
    """Test actual entity ID generation in integration."""

    @pytest.mark.asyncio
    async def test_number_entity_unique_id_format(self, hass):
        """Test that number entities get correct unique_id format."""
        # Create a proper mock config entry for global configuration
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Solar Window System",
            data={"entry_type": "global"},
            entry_id="test_global_entry"
        )
        config_entry.add_to_hass(hass)

        # Create device registry and add global device
        device_registry = dr.async_get(hass)
        global_device = device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System Global Configuration",
            manufacturer="Solar Window System",
            model="Global Configuration",
        )

        # Mock entity addition to capture entities
        added_entities = []

        def mock_add_entities(new_entities, update_before_add=False):
            added_entities.extend(new_entities)

        # Set up number entities
        await async_setup_entry(hass, config_entry, mock_add_entities)

        # Verify entities were created
        assert len(added_entities) > 0, "No number entities were created"

        # Check entity unique_id format
        expected_number_entities = [
            key
            for key, config in GLOBAL_CONFIG_ENTITIES.items()
            if config["platform"] == "input_number"
        ]

        assert len(added_entities) == len(expected_number_entities), (
            f"Expected {len(expected_number_entities)} number entities, "
            f"got {len(added_entities)}"
        )

        # Verify each entity has correct unique_id format
        for entity in added_entities:
            unique_id = entity._attr_unique_id
            assert unique_id.startswith(ENTITY_PREFIX), (
                f"Entity unique_id '{unique_id}' should start with '{ENTITY_PREFIX}'"
            )
            assert "_global_" in unique_id, (
                f"Entity unique_id '{unique_id}' should contain '_global_'"
            )

        # Verify specific entity unique_ids
        entity_unique_ids = {
            entity._entity_key: entity._attr_unique_id for entity in added_entities
        }

        for entity_key in expected_number_entities:
            expected_unique_id = f"{ENTITY_PREFIX}_global_{entity_key}"
            assert entity_key in entity_unique_ids, (
                f"Entity {entity_key} not found in created entities"
            )
            assert entity_unique_ids[entity_key] == expected_unique_id, (
                f"Entity {entity_key} has unique_id '{entity_unique_ids[entity_key]}', "
                f"expected '{expected_unique_id}'"
            )

    @pytest.mark.asyncio
    async def test_entity_registry_integration(self, hass):
        """Test that entities registered with entity registry get correct entity_id."""
        # Create config entry
        config_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Solar Window System",
            data={"entry_type": "global"},
            entry_id="test_global_entry"
        )
        config_entry.add_to_hass(hass)

        # Create device
        device_registry = dr.async_get(hass)
        global_device = device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, "global_config")},
            name="Solar Window System Global Configuration",
            manufacturer="Solar Window System",
            model="Global Configuration",
        )

        # Create and register entities manually to test entity_id generation
        entity_registry = er.async_get(hass)

        # Test one specific entity
        test_entity_key = "window_g_value"  # First input_number entity
        test_config = GLOBAL_CONFIG_ENTITIES[test_entity_key]

        unique_id = f"{ENTITY_PREFIX}_global_{test_entity_key}"
        entity_id = f"number.{unique_id}"

        # Register entity
        entity_entry = entity_registry.async_get_or_create(
            domain="number",
            platform=DOMAIN,
            unique_id=unique_id,
            config_entry=config_entry,
            device_id=global_device.id,
            original_name=test_config["name"],
        )

        # Verify entity_id follows expected pattern
        assert entity_entry.entity_id == entity_id, (
            f"Entity ID '{entity_entry.entity_id}' should be '{entity_id}'"
        )

        # Verify it starts with "number.sws_"
        expected_prefix = f"number.{ENTITY_PREFIX}_"
        assert entity_entry.entity_id.startswith(expected_prefix), (
            f"Entity ID '{entity_entry.entity_id}' should start with '{expected_prefix}'"
        )
