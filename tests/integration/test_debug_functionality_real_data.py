"""
Integration test for debug functionality using real HA instance data.

This test analyzes the actual entity registry and sensor states to understand
why current_sensor_states sections are empty in debug output.
"""

import json
from pathlib import Path
from typing import Any

from custom_components.solar_window_system.calculator import SolarWindowCalculator
from custom_components.solar_window_system.const import DOMAIN


class TestDebugFunctionalityRealData:
    """Test debug functionality with real HA instance data."""

    def load_debug_json(self, filename: str):
        """Load debug JSON file and return parsed data."""
        debug_path = Path("/workspaces/hass-solar-window-system/config") / filename
        with debug_path.open() as f:
            return json.load(f)

    def extract_entity_info_from_debug(
        self, debug_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract entity information from debug JSON."""
        return {
            "window_id": debug_data.get("window_id"),
            "configuration": debug_data.get("configuration", {}),
            "current_sensor_states": debug_data.get("current_sensor_states", {}),
            "debug_info": debug_data.get("current_sensor_states", {}).get(
                "debug_info", {}
            ),
            "total_entities_in_registry": debug_data.get("current_sensor_states", {})
            .get("debug_info", {})
            .get("total_entities_in_registry", 0),
            "sample_entities": debug_data.get("current_sensor_states", {})
            .get("debug_info", {})
            .get("sample_entities", []),
            "search_attempts": debug_data.get("current_sensor_states", {})
            .get("debug_info", {})
            .get("search_attempts", []),
        }

    def analyze_missing_entities(self, debug_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze which entities are missing and why."""
        sensor_states = debug_data.get("current_sensor_states", {})
        debug_info = sensor_states.get("debug_info", {})

        analysis = {
            "window_level_found": len(sensor_states.get("window_level", {})),
            "group_level_found": len(sensor_states.get("group_level", {})),
            "global_level_found": len(sensor_states.get("global_level", {})),
            "total_found": debug_info.get("entities_found", 0),
            "search_attempts": len(debug_info.get("search_attempts", [])),
            "missing_levels": [],
            "expected_patterns": [],
        }

        # Check which levels are empty
        if analysis["window_level_found"] == 0:
            analysis["missing_levels"].append("window_level")
        if analysis["group_level_found"] == 0:
            analysis["missing_levels"].append("group_level")
        if analysis["global_level_found"] == 0:
            analysis["missing_levels"].append("global_level")

        # Generate expected entity patterns
        config = debug_data.get("configuration", {})
        window_config = config.get("window_config", {})
        group_config = config.get("group_config", {})

        window_name = window_config.get("name", "unknown")
        group_name = group_config.get("name", "unknown")

        # Window level patterns
        window_patterns = [
            f"sensor.sws_window_{window_name}_total_power",
            f"sensor.sws_window_{window_name}_total_power_direct",
            f"sensor.sws_window_{window_name}_total_power_diffuse",
            f"sensor.sws_window_{window_name}_power_m2_total",
            f"sensor.sws_window_{window_name}_power_m2_direct",
            f"sensor.sws_window_{window_name}_power_m2_diffuse",
            f"sensor.sws_window_{window_name}_power_m2_raw",
            f"sensor.sws_window_{window_name}_total_power_raw",
        ]

        # Group level patterns
        group_patterns = [
            f"sensor.sws_group_{group_name}_total_power",
            f"sensor.sws_group_{group_name}_total_power_direct",
            f"sensor.sws_group_{group_name}_total_power_diffuse",
        ]

        # Global level patterns
        global_patterns = [
            "sensor.sws_global_total_power",
            "sensor.sws_global_total_power_direct",
            "sensor.sws_global_total_power_diffuse",
            "sensor.sws_global_windows_with_shading",
            "sensor.sws_global_window_count",
            "sensor.sws_global_shading_count",
        ]

        analysis["expected_patterns"] = {
            "window": window_patterns,
            "group": group_patterns,
            "global": global_patterns,
        }

        return analysis

    def test_real_debug_data_analysis(self):
        """Test analysis of real debug data to understand missing entities."""
        # Load the latest debug file
        debug_files = list(
            Path("/workspaces/hass-solar-window-system/config").glob("debug_*.json")
        )
        if not debug_files:
            pytest.skip("No debug files found")

        latest_debug = max(debug_files, key=lambda p: p.stat().st_mtime)
        debug_data = self.load_debug_json(latest_debug.name)

        print(f"\n=== ANALYZING DEBUG FILE: {latest_debug.name} ===")

        # Extract and analyze data
        entity_info = self.extract_entity_info_from_debug(debug_data)
        analysis = self.analyze_missing_entities(debug_data)

        print(f"Window ID: {entity_info['window_id']}")
        print(
            f"Total entities in registry: {entity_info['total_entities_in_registry']}"
        )
        print(f"Entities found: {analysis['total_found']}")
        print(f"Search attempts: {analysis['search_attempts']}")

        print(f"\n=== SENSOR LEVELS ===")
        print(f"Window level: {analysis['window_level_found']} entities")
        print(f"Group level: {analysis['group_level_found']} entities")
        print(f"Global level: {analysis['global_level_found']} entities")

        print(f"\n=== MISSING LEVELS ===")
        if analysis["missing_levels"]:
            for level in analysis["missing_levels"]:
                print(f"❌ {level} is empty")
        else:
            print("✅ All levels have data")

        print(f"\n=== SAMPLE ENTITIES FROM REGISTRY ===")
        for entity in entity_info["sample_entities"][:5]:
            print(f"  {entity['entity_id']} (name: {entity.get('name', 'None')})")

        print(f"\n=== EXPECTED PATTERNS ===")
        for level, patterns in analysis["expected_patterns"].items():
            print(f"\n{level.upper()} LEVEL:")
            for pattern in patterns:
                print(f"  {pattern}")

        print(f"\n=== SEARCH ATTEMPTS ===")
        for attempt in entity_info["search_attempts"][:10]:
            print(
                f"  Searched: '{attempt['searched_name']}' (level: {attempt['level']})"
            )

        # Assertions
        assert entity_info["total_entities_in_registry"] > 0, (
            "Entity registry should not be empty"
        )
        assert analysis["search_attempts"] > 0, "Search attempts should be recorded"

        # This test will help us understand what's actually in the registry
        # and why our search patterns might not be working

    def test_entity_search_patterns(self):
        """Test different entity search patterns to find the correct ones."""
        debug_files = list(
            Path("/workspaces/hass-solar-window-system/config").glob("debug_*.json")
        )
        if not debug_files:
            pytest.skip("No debug files found")

        latest_debug = max(debug_files, key=lambda p: p.stat().st_mtime)
        debug_data = self.load_debug_json(latest_debug.name)

        entity_info = self.extract_entity_info_from_debug(debug_data)
        sample_entities = entity_info["sample_entities"]

        print("\n=== TESTING ENTITY SEARCH PATTERNS ===")

        # Test different search patterns
        sws_entities = [e for e in sample_entities if "sws" in e["entity_id"].lower()]
        sensor_entities = [
            e for e in sample_entities if e["entity_id"].startswith("sensor.")
        ]

        print(f"SWS entities in sample: {len(sws_entities)}")
        print(f"Sensor entities in sample: {len(sensor_entities)}")

        for entity in sws_entities:
            print(f"  Found SWS entity: {entity['entity_id']}")

        for entity in sensor_entities:
            print(f"  Found sensor entity: {entity['entity_id']}")

        # If we find SWS entities, our search patterns might be correct
        # If we don't find any, then the entities might have different naming

    def test_comprehensive_debug_validation(self):
        """Comprehensive test to validate all expected data is present in debug JSON."""
        debug_files = list(
            Path("/workspaces/hass-solar-window-system/config").glob("debug_*.json")
        )
        if not debug_files:
            pytest.skip("No debug files found")

        latest_debug = max(debug_files, key=lambda p: p.stat().st_mtime)
        debug_data = self.load_debug_json(latest_debug.name)

        print(f"\n=== COMPREHENSIVE DEBUG VALIDATION ===")

        # Check all required sections
        required_sections = [
            "timestamp",
            "window_id",
            "configuration",
            "sensor_data",
            "calculated_sensors",
            "current_sensor_states",
            "metadata",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in debug_data:
                missing_sections.append(section)

        if missing_sections:
            print(f"❌ Missing sections: {missing_sections}")
        else:
            print("✅ All required sections present")

        # Validate current_sensor_states structure
        sensor_states = debug_data.get("current_sensor_states", {})
        required_levels = ["window_level", "group_level", "global_level"]

        for level in required_levels:
            if level not in sensor_states:
                print(f"❌ Missing {level} in current_sensor_states")
            else:
                count = len(sensor_states[level])
                print(f"✅ {level}: {count} entities")

        # Check if debug_info is present and has required fields
        debug_info = sensor_states.get("debug_info", {})
        required_debug_fields = [
            "window_id",
            "entity_registry_available",
            "entities_found",
            "search_attempts",
            "total_entities_in_registry",
        ]

        for field in required_debug_fields:
            if field not in debug_info:
                print(f"❌ Missing debug_info field: {field}")
            else:
                print(f"✅ debug_info.{field}: {debug_info[field]}")

        # Validate that we have meaningful data
        assert "current_sensor_states" in debug_data, (
            "current_sensor_states section must exist"
        )
        assert "debug_info" in sensor_states, "debug_info must be present"

        # This test should fail initially, showing us exactly what's missing
        # Then we can fix the implementation based on the findings
