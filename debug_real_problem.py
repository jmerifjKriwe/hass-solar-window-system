#!/usr/bin/env python3
"""Debug script to reproduce the real 'expected str' problem in Options Flow."""

import json
import sys
import voluptuous as vol
from homeassistant.helpers import selector

# Simulate the real stored options from the registry (numeric types!)
REAL_STORED_OPTIONS = {
    "diffuse_factor": 0.15,  # float, not string!
    "frame_width": 0.125,  # float, not string!
    "g_value": 0.5,  # float, not string!
    "temperature_indoor_base": 23.0,  # float, not string!
    "temperature_outdoor_base": 19.5,  # float, not string!
    "threshold_diffuse": 150,  # int, not string!
    "threshold_direct": 200,  # int, not string!
    "tilt": 90,  # int, not string!
}


def test_wrong_schema_building():
    """Test the WRONG way (how it was before) - this should cause the error."""
    print("=== Testing WRONG schema building (before fix) ===")

    schema_dict = {}

    for key in ["diffuse_factor", "threshold_direct", "tilt"]:
        # This is how the values actually come from the registry
        cur_val = REAL_STORED_OPTIONS.get(key, "")

        # Convert to string for suggested_value
        suggested_str = "" if cur_val in ("", None) else str(cur_val)

        print(f"Key: {key}")
        print(f"  cur_val: {cur_val} (type: {type(cur_val)})")
        print(f"  suggested_str: {suggested_str} (type: {type(suggested_str)})")

        # WRONG WAY (the bug):
        try:
            schema_dict[key] = vol.Optional(
                str, description={"suggested_value": suggested_str}
            )
            print(f"  ❌ Wrong schema creation succeeded (shouldn't happen)")
        except Exception as e:
            print(f"  ❌ Wrong schema creation failed: {e}")

        print()


def test_correct_schema_building():
    """Test the CORRECT way (after fix) - this should work."""
    print("=== Testing CORRECT schema building (after fix) ===")

    schema_dict = {}

    for key in ["diffuse_factor", "threshold_direct", "tilt"]:
        # This is how the values actually come from the registry
        cur_val = REAL_STORED_OPTIONS.get(key, "")

        # Convert to string for suggested_value
        suggested_str = "" if cur_val in ("", None) else str(cur_val)

        print(f"Key: {key}")
        print(f"  cur_val: {cur_val} (type: {type(cur_val)})")
        print(f"  suggested_str: {suggested_str} (type: {type(suggested_str)})")

        # CORRECT WAY (the fix):
        try:
            schema_dict[
                vol.Optional(key, description={"suggested_value": suggested_str})
            ] = str
            print(f"  ✅ Correct schema creation succeeded")
        except Exception as e:
            print(f"  ❌ Correct schema creation failed: {e}")

        print()

    # Test schema validation
    print("Testing schema validation with real data...")
    try:
        schema = vol.Schema(schema_dict)

        # Simulate user input (strings from form)
        user_input = {"diffuse_factor": "0.15", "threshold_direct": "200", "tilt": "90"}

        result = schema(user_input)
        print(f"✅ Schema validation succeeded: {result}")

    except Exception as e:
        print(f"❌ Schema validation failed: {e}")


def test_suggested_value_issue():
    """Test if the suggested_value parameter causes issues with non-string values."""
    print("\n=== Testing suggested_value parameter directly ===")

    # Test different types of suggested values
    test_cases = [
        ("string_value", "test"),
        ("float_value", 0.15),
        ("int_value", 200),
        ("converted_float", str(0.15)),
        ("converted_int", str(200)),
    ]

    for case_name, suggested_val in test_cases:
        print(f"\nTesting {case_name}: {suggested_val} (type: {type(suggested_val)})")

        try:
            # Try creating vol.Optional with different suggested_value types
            field = vol.Optional(
                "test_field", description={"suggested_value": suggested_val}
            )

            schema = vol.Schema({field: str})

            # Test with string input
            result = schema({"test_field": "user_input"})
            print(f"  ✅ Success: {result}")

        except Exception as e:
            print(f"  ❌ Failed: {e}")


if __name__ == "__main__":
    test_wrong_schema_building()
    test_correct_schema_building()
    test_suggested_value_issue()
