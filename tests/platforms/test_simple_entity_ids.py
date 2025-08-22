"""Simple test to verify entity ID generation works correctly."""

from custom_components.solar_window_system.const import ENTITY_PREFIX
from custom_components.solar_window_system.number import GlobalConfigNumberEntity


class TestEntityIDGenerationSimple:
    def test_number_entity_unique_id(self) -> None:
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

        class MockDevice:
            def __init__(self):
                self.identifiers = {("solar_window_system", "global_config")}
                self.name = "Test Device"
                self.manufacturer = "Test"
                self.model = "Test"

        device = MockDevice()
        entity = GlobalConfigNumberEntity(entity_key, config, device)
        expected_unique_id = f"{ENTITY_PREFIX}_global_{entity_key}"
        assert entity._attr_unique_id == expected_unique_id
        assert entity._attr_unique_id.startswith(ENTITY_PREFIX)
        expected_entity_id = f"number.{expected_unique_id}"
        assert expected_entity_id.startswith(f"number.{ENTITY_PREFIX}_")

    def test_all_global_config_entities_have_prefix(self) -> None:
        from custom_components.solar_window_system.const import GLOBAL_CONFIG_ENTITIES
        from custom_components.solar_window_system.const import ENTITY_PREFIX

        for entity_key, config in GLOBAL_CONFIG_ENTITIES.items():
            platform = config["platform"]
            if platform == "input_number":
                ha_platform = "number"
            elif platform == "input_text":
                ha_platform = "text"
            elif platform == "input_select":
                ha_platform = "select"
            elif platform == "input_boolean":
                ha_platform = "switch"
            else:
                ha_platform = platform

            expected_unique_id = f"{ENTITY_PREFIX}_global_{entity_key}"
            expected_entity_id = f"{ha_platform}.{expected_unique_id}"
            assert expected_entity_id.startswith(f"{ha_platform}.{ENTITY_PREFIX}_")
