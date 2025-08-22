"""Tests for entity ID generation and prefix application."""

from custom_components.solar_window_system.const import (
    ENTITY_PREFIX,
    GLOBAL_CONFIG_ENTITIES,
)

# Constants for expected values
EXPECTED_TOTAL_ENTITIES = 11
EXPECTED_NUMBER_ENTITIES = 3
EXPECTED_TEXT_ENTITIES = 1
EXPECTED_SELECT_ENTITIES = 0
EXPECTED_BOOLEAN_ENTITIES = 3
EXPECTED_SENSOR_ENTITIES = 4
EXPECTED_DEBUG_ENTITIES = 1


class TestEntityIdGeneration:
    """Test entity ID generation and naming conventions."""

    def test_entity_prefix_constant(self) -> None:
        expected_prefix = "sws"
        if expected_prefix != ENTITY_PREFIX:
            raise AssertionError(
                f"Entity prefix should be '{expected_prefix}', got '{ENTITY_PREFIX}'"
            )

    def test_unique_id_format(self) -> None:
        for entity_key in GLOBAL_CONFIG_ENTITIES:
            expected_unique_id = f"{ENTITY_PREFIX}_global_{entity_key}"
            if not expected_unique_id.startswith(ENTITY_PREFIX):
                raise AssertionError(
                    f"Unique ID {expected_unique_id} should start with {ENTITY_PREFIX}"
                )
            if "_global_" not in expected_unique_id:
                raise AssertionError(
                    f"Unique ID {expected_unique_id} should contain '_global_'"
                )
            if not expected_unique_id.endswith(entity_key):
                raise AssertionError(
                    f"Unique ID {expected_unique_id} should end with {entity_key}"
                )

    def test_expected_entity_ids(self) -> None:
        expected_entity_ids = {}
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
            expected_entity_ids[entity_key] = (
                f"{platform}.{ENTITY_PREFIX}_global_{entity_key}"
            )

        for entity_key, expected_entity_id in expected_entity_ids.items():
            if "." not in expected_entity_id:
                raise AssertionError(
                    f"Entity ID {expected_entity_id} should contain '.'"
                )
            platform, name_part = expected_entity_id.split(".", 1)
            valid_platforms = ["number", "text", "select", "switch", "sensor"]
            if platform not in valid_platforms:
                raise AssertionError(
                    f"Platform {platform} should be one of {valid_platforms}"
                )
            expected_name = f"{ENTITY_PREFIX}_global_{entity_key}"
            if name_part != expected_name:
                raise AssertionError(f"Name part {name_part} should be {expected_name}")

    def test_global_config_entities_structure(self) -> None:
        actual_count = len(GLOBAL_CONFIG_ENTITIES)
        if actual_count != EXPECTED_TOTAL_ENTITIES:
            raise AssertionError(
                f"Expected {EXPECTED_TOTAL_ENTITIES} entities, got {actual_count}"
            )

        platform_counts = {
            "input_number": 0,
            "input_text": 0,
            "input_select": 0,
            "input_boolean": 0,
            "sensor": 0,
        }
        debug_entities = 0

        for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
            required_fields = ["platform", "name", "default"]
            for field in required_fields:
                if field not in config:
                    raise AssertionError(
                        f"Entity {entity_key} missing required field: {field}"
                    )
            platform = config["platform"]
            if platform not in platform_counts:
                raise AssertionError(f"Unknown platform: {platform}")
            platform_counts[platform] += 1
            if config.get("category") == "debug":
                debug_entities += 1

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
                raise AssertionError(
                    f"Expected {expected_count} {platform} entities, got {actual_count}"
                )

        if debug_entities != EXPECTED_DEBUG_ENTITIES:
            raise AssertionError(
                f"Expected {EXPECTED_DEBUG_ENTITIES} debug entities, got {debug_entities}"
            )

        total_entities = sum(platform_counts.values())
        if total_entities != EXPECTED_TOTAL_ENTITIES:
            raise AssertionError(
                f"Total entities {total_entities} should equal {EXPECTED_TOTAL_ENTITIES}"
            )

    def test_entity_unique_id_uniqueness(self) -> None:
        unique_ids = [
            f"{ENTITY_PREFIX}_global_{entity_key}"
            for entity_key in GLOBAL_CONFIG_ENTITIES
        ]
        if len(unique_ids) != len(set(unique_ids)):
            raise AssertionError("Found duplicate unique IDs")

    def test_debug_entity_identification(self) -> None:
        debug_entities = [
            entity_key
            for entity_key, config in GLOBAL_CONFIG_ENTITIES.items()
            if config.get("category") == "debug"
        ]
        if len(debug_entities) != EXPECTED_DEBUG_ENTITIES:
            raise AssertionError(
                f"Expected {EXPECTED_DEBUG_ENTITIES} debug entity, got {len(debug_entities)}"
            )
        if "debug" not in debug_entities:
            raise AssertionError("Expected 'debug' entity to be marked as debug")
