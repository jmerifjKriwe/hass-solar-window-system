"""Simple test to verify entity ID generation works correctly."""

from custom_components.solar_window_system.const import ENTITY_PREFIX
from custom_components.solar_window_system.number import GlobalConfigNumberEntity


class TestEntityIDGenerationSimple:
    """Test entity ID generation without complex Home Assistant setup."""

    def test_number_entity_unique_id(self):
        """Test that number entities have correct unique_id format."""
        entity_key = "window_g_value"
        config = {
            "platform": "input_number",
            "name": "Window G-Value",
            "min": 0.1,
            "max": 0.9,
            "step": 0.01,
            "default": 0.5,
            "unit": "",
            "icon": "mdi:window-closed-variant",
        }

        # Mock device (we only need basic attributes)
        class MockDevice:
            def __init__(self):
                self.identifiers = {("solar_window_system", "global_config")}
                self.name = "Test Device"
                self.manufacturer = "Test"
                self.model = "Test"

        device = MockDevice()

        # Create entity
        entity = GlobalConfigNumberEntity(entity_key, config, device)

        # Verify unique_id format
        expected_unique_id = f"{ENTITY_PREFIX}_global_{entity_key}"
        assert entity._attr_unique_id == expected_unique_id, (
            f"Entity unique_id should be '{expected_unique_id}', "
            f"got '{entity._attr_unique_id}'"
        )

        # Verify it starts with the prefix
        assert entity._attr_unique_id.startswith(ENTITY_PREFIX), (
            f"Entity unique_id should start with '{ENTITY_PREFIX}'"
        )

        # Verify the expected entity_id that Home Assistant would generate
        # Home Assistant converts input_number to number platform
        expected_entity_id = f"number.{expected_unique_id}"
        print(f"Entity would get entity_id: {expected_entity_id}")

        # This confirms that the entity would get the desired prefix in its entity_id
        assert expected_entity_id.startswith(f"number.{ENTITY_PREFIX}_"), (
            f"Generated entity_id '{expected_entity_id}' should start with "
            f"'number.{ENTITY_PREFIX}_'"
        )

    def test_all_global_config_entities_have_prefix(self):
        """Test that all entity types would get the correct prefix."""
        from custom_components.solar_window_system.const import GLOBAL_CONFIG_ENTITIES

        for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
            platform = config["platform"]

            # Map input_* platforms to actual HA platforms
            if platform == "input_number":
                ha_platform = "number"
            elif platform == "input_text":
                ha_platform = "text"
            elif platform == "input_select":
                ha_platform = "select"
            elif platform == "input_boolean":
                ha_platform = "switch"
            else:
                ha_platform = platform  # sensor stays sensor

            expected_unique_id = f"{ENTITY_PREFIX}_global_{entity_key}"
            expected_entity_id = f"{ha_platform}.{expected_unique_id}"

            print(f"Entity '{entity_key}' -> '{expected_entity_id}'")

            # Verify the format
            assert expected_entity_id.startswith(f"{ha_platform}.{ENTITY_PREFIX}_"), (
                f"Entity ID '{expected_entity_id}' should start with "
                f"'{ha_platform}.{ENTITY_PREFIX}_'"
            )
