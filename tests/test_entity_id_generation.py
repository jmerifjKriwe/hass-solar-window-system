"""Tests for entity ID generation and prefix application."""

import pytest

from custom_components.solar_window_system.const import (
    ENTITY_PREFIX,
    GLOBAL_CONFIG_ENTITIES,
)

# Constants for expected values
EXPECTED_TOTAL_ENTITIES = 23
EXPECTED_NUMBER_ENTITIES = 14  # input_number entities
EXPECTED_TEXT_ENTITIES = 1  # input_text entities
EXPECTED_SELECT_ENTITIES = 2  # input_select entities
EXPECTED_BOOLEAN_ENTITIES = 2  # input_boolean entities
EXPECTED_SENSOR_ENTITIES = 4  # sensor entities
EXPECTED_DEBUG_ENTITIES = 1


class TestEntityIdGeneration:
    """Test entity ID generation and naming conventions."""

    def test_entity_prefix_constant(self) -> None:
        """Test that entity prefix constant is correctly defined."""
        expected_prefix = "sws"
        if ENTITY_PREFIX != expected_prefix:
            msg = f"Entity prefix should be '{expected_prefix}', got '{ENTITY_PREFIX}'"
            raise AssertionError(msg)

    def test_unique_id_format(self) -> None:
        """Test that unique IDs follow the expected format."""
        for entity_key in GLOBAL_CONFIG_ENTITIES:
            expected_unique_id = f"{ENTITY_PREFIX}_global_{entity_key}"

            # Test that the format is correct
            if not expected_unique_id.startswith(ENTITY_PREFIX):
                msg = (
                    f"Unique ID {expected_unique_id} should start with {ENTITY_PREFIX}"
                )
                raise AssertionError(msg)

            if "_global_" not in expected_unique_id:
                msg = f"Unique ID {expected_unique_id} should contain '_global_'"
                raise AssertionError(msg)

            if not expected_unique_id.endswith(entity_key):
                msg = f"Unique ID {expected_unique_id} should end with {entity_key}"
                raise AssertionError(msg)

    def test_expected_entity_ids(self) -> None:
        """Test that entity IDs are generated as expected."""
        expected_entity_ids = {}

        for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
            platform = config["platform"]

            # Map platform types to actual Home Assistant platforms
            if platform == "input_number":
                platform = "number"
            elif platform == "input_text":
                platform = "text"
            elif platform == "input_select":
                platform = "select"
            elif platform == "input_boolean":
                platform = "switch"

            expected_entity_ids[entity_key] = (
                f"{platform}.{ENTITY_PREFIX}_global_{entity_key}"
            )

        # Verify all entities have expected format
        for entity_key, expected_entity_id in expected_entity_ids.items():
            if "." not in expected_entity_id:
                msg = f"Entity ID {expected_entity_id} should contain '.'"
                raise AssertionError(msg)

            platform, name_part = expected_entity_id.split(".", 1)
            valid_platforms = ["number", "text", "select", "switch", "sensor"]

            if platform not in valid_platforms:
                msg = f"Platform {platform} should be one of {valid_platforms}"
                raise AssertionError(msg)

            expected_name = f"{ENTITY_PREFIX}_global_{entity_key}"
            if name_part != expected_name:
                msg = f"Name part {name_part} should be {expected_name}"
                raise AssertionError(msg)

    def test_global_config_entities_structure(self) -> None:
        """Test that GLOBAL_CONFIG_ENTITIES has the expected structure."""
        actual_count = len(GLOBAL_CONFIG_ENTITIES)
        if actual_count != EXPECTED_TOTAL_ENTITIES:
            msg = f"Expected {EXPECTED_TOTAL_ENTITIES} entities, got {actual_count}"
            raise AssertionError(msg)

        # Count entities by platform
        platform_counts = {
            "input_number": 0,
            "input_text": 0,
            "input_select": 0,
            "input_boolean": 0,
            "sensor": 0,
        }

        debug_entities = 0

        for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
            # Verify required fields
            required_fields = ["platform", "name", "default"]
            for field in required_fields:
                if field not in config:
                    msg = f"Entity {entity_key} missing required field: {field}"
                    raise AssertionError(msg)

            # Count by platform
            platform = config["platform"]
            if platform not in platform_counts:
                msg = f"Unknown platform: {platform}"
                raise AssertionError(msg)
            platform_counts[platform] += 1

            # Count debug entities
            if config.get("category") == "debug":
                debug_entities += 1

        # Verify we have the expected distribution
        expected_counts = {
            "input_number": EXPECTED_NUMBER_ENTITIES,
            "input_text": EXPECTED_TEXT_ENTITIES,
            "input_select": EXPECTED_SELECT_ENTITIES,
            "input_boolean": EXPECTED_BOOLEAN_ENTITIES,
            "sensor": EXPECTED_SENSOR_ENTITIES,
        }

        for platform, expected_count in expected_counts.items():
            actual_count = platform_counts[platform]
            if actual_count != expected_count:
                msg = (
                    f"Expected {expected_count} {platform} entities, got {actual_count}"
                )
                raise AssertionError(msg)

        if debug_entities != EXPECTED_DEBUG_ENTITIES:
            msg = f"Expected {EXPECTED_DEBUG_ENTITIES} debug entities, got {debug_entities}"
            raise AssertionError(msg)

        # Verify total
        total_entities = sum(platform_counts.values())
        if total_entities != EXPECTED_TOTAL_ENTITIES:
            msg = f"Total entities {total_entities} should equal {EXPECTED_TOTAL_ENTITIES}"
            raise AssertionError(msg)

    def test_entity_unique_id_uniqueness(self) -> None:
        """Test that all entity unique IDs are unique."""
        unique_ids = []

        for entity_key in GLOBAL_CONFIG_ENTITIES:
            unique_id = f"{ENTITY_PREFIX}_global_{entity_key}"
            unique_ids.append(unique_id)

        # Verify no duplicates
        unique_set = set(unique_ids)
        if len(unique_ids) != len(unique_set):
            msg = "Found duplicate unique IDs"
            raise AssertionError(msg)

    def test_debug_entity_identification(self) -> None:
        """Test that debug entities are correctly identified."""
        debug_entities = []

        for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
            if config.get("category") == "debug":
                debug_entities.append(entity_key)

        # Should have exactly one debug entity
        if len(debug_entities) != EXPECTED_DEBUG_ENTITIES:
            msg = f"Expected {EXPECTED_DEBUG_ENTITIES} debug entity, got {len(debug_entities)}"
            raise AssertionError(msg)

        if "debug" not in debug_entities:
            msg = "Expected 'debug' entity to be marked as debug"
            raise AssertionError(msg)
