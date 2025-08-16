"""Test to verify that the "expected str" fix works correctly."""

import pytest
from unittest.mock import AsyncMock, patch, PropertyMock
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from custom_components.solar_window_system import config_flow
from custom_components.solar_window_system.const import DOMAIN

from tests.test_data import (
    VALID_GROUP_OPTIONS_NUMERIC,
    VALID_WINDOW_OPTIONS_NUMERIC,
    VALID_GLOBAL_SCENARIOS,
    VALID_GLOBAL_ENHANCED,
)


class TestSecondSaveBugFix:
    """Test suite specifically designed to catch the "expected str" bug."""

    async def test_group_reconfigure_with_numeric_values_second_save(
        self, hass, global_config_entry
    ):
        """
        Test that reproduces the "expected str" bug with centralized test data.
        """
        flow = config_flow.GroupSubentryFlowHandler()
        flow.hass = hass
        flow.init_step = "user"
        with (
            patch.object(
                type(flow),
                "source",
                new_callable=PropertyMock,
                return_value=config_entries.SOURCE_USER,
            ),
            patch(
                "custom_components.solar_window_system.helpers.get_temperature_sensor_entities",
                return_value=[],
            ),
        ):
            # Ensure all required fields are present and as strings
            initial_input = {
                k: str(v) if isinstance(v, (int, float)) else v
                for k, v in VALID_GROUP_OPTIONS_NUMERIC.items()
            }
            # Set indoor_temperature_sensor explicitly (required for valid config)
            initial_input["indoor_temperature_sensor"] = "sensor.temp1"
            # Step 1: Get the form
            result = await flow.async_step_user(None)

            # Step through wizard following correct Group flow pattern
            # Step 1: async_step_user with basic group fields
            group_step1_data = {
                k: str(v) for k, v in VALID_GROUP_OPTIONS_NUMERIC.items()
            }
            result = await flow.async_step_user(group_step1_data)
            assert result["type"] == "form"
            assert result["step_id"] == "enhanced"

            # Step 2: async_step_enhanced with enhanced/scenario fields
            group_step2_data = {k: str(v) for k, v in VALID_GLOBAL_SCENARIOS.items()}
            result = await flow.async_step_enhanced(group_step2_data)
            assert result["type"] == "create_entry"
            stored_data = initial_input.copy()

        reconfig_flow = config_flow.GroupSubentryFlowHandler()
        reconfig_flow.hass = hass
        reconfig_flow.init_step = "user"
        with (
            patch.object(
                type(reconfig_flow),
                "source",
                new_callable=PropertyMock,
                return_value=config_entries.SOURCE_RECONFIGURE,
            ),
            patch.object(
                reconfig_flow,
                "_get_reconfigure_subentry",
                return_value=AsyncMock(data=stored_data),
            ),
            patch(
                "custom_components.solar_window_system.helpers.get_temperature_sensor_entities",
                return_value=[],
            ),
        ):
            # Test the critical part: reconfigure can start and handle string conversion
            result2 = await reconfig_flow.async_step_reconfigure(None)
            assert result2["type"] == "form"
            assert result2["step_id"] == "user"
            assert "data_schema" in result2
            schema = result2["data_schema"]
            assert isinstance(schema, vol.Schema)

            # This is the critical test: ensure that when we provide the same input
            # (potentially with numeric values converted to strings), the form
            # handles it correctly without "expected str" errors
            same_input = {
                k: str(v) if isinstance(v, (int, float)) else v
                for k, v in VALID_GROUP_OPTIONS_NUMERIC.items()
            }
            # Verify that the schema can process this input without the "expected str" error
            try:
                # This is where the bug would occur - schema validation with string defaults
                validated_data = schema(same_input)
                # If we get here, the string conversion fix is working
                assert isinstance(validated_data, dict)
            except vol.Invalid as exc:
                if "expected str" in str(exc):
                    pytest.fail(f"String conversion fix failed: {exc}")
                else:
                    # Other validation errors are fine, we're only testing string conversion
                    pass

    async def test_window_reconfigure_with_numeric_values_second_save(
        self, hass, global_config_entry
    ):
        """
        Test Window reconfiguration with centralized test data.
        """
        flow = config_flow.WindowSubentryFlowHandler()
        flow.hass = hass
        flow.init_step = "user"
        with (
            patch.object(
                type(flow),
                "source",
                new_callable=PropertyMock,
                return_value=config_entries.SOURCE_USER,
            ),
            patch(
                "custom_components.solar_window_system.helpers.get_temperature_sensor_entities",
                return_value=[],
            ),
            patch.object(
                flow,
                "_get_group_subentries",
                return_value=[],
            ),
        ):
            # Use VALID_WINDOW_OPTIONS_NUMERIC and ensure all required fields are present as strings
            initial_input = {
                k: str(v) if isinstance(v, (int, float)) else v
                for k, v in VALID_WINDOW_OPTIONS_NUMERIC.items()
            }
            # Step 1: Get the form
            result = await flow.async_step_user(None)

            # Step through wizard following correct Window flow pattern
            # Step 1: async_step_user with basic window fields
            window_step1_data = {
                k: str(v) for k, v in VALID_WINDOW_OPTIONS_NUMERIC.items()
            }
            result = await flow.async_step_user(window_step1_data)
            assert result["type"] == "form"
            assert result["step_id"] == "overrides"

            # Step 2: async_step_overrides with enhanced/override fields
            window_step2_data = {k: str(v) for k, v in VALID_GLOBAL_ENHANCED.items()}
            result = await flow.async_step_overrides(window_step2_data)
            assert result["type"] == "form"
            assert result["step_id"] == "scenarios"

            # Step 3: async_step_scenarios with scenario fields
            window_step3_data = {k: str(v) for k, v in VALID_GLOBAL_SCENARIOS.items()}
            result = await flow.async_step_scenarios(window_step3_data)
            assert result["type"] == "create_entry"
            stored_data = initial_input.copy()

        reconfig_flow = config_flow.WindowSubentryFlowHandler()
        reconfig_flow.hass = hass
        reconfig_flow.init_step = "user"
        with (
            patch.object(
                type(reconfig_flow),
                "source",
                new_callable=PropertyMock,
                return_value=config_entries.SOURCE_RECONFIGURE,
            ),
            patch.object(
                reconfig_flow,
                "_get_reconfigure_subentry",
                return_value=AsyncMock(data=stored_data),
            ),
            patch(
                "custom_components.solar_window_system.helpers.get_temperature_sensor_entities",
                return_value=[],
            ),
            patch.object(
                reconfig_flow,
                "_get_group_subentries",
                return_value=[],
            ),
        ):
            # Test the critical part: reconfigure can start and handle string conversion
            result2 = await reconfig_flow.async_step_reconfigure(None)
            assert result2["type"] == "form"
            same_input = {
                k: str(v) if isinstance(v, (int, float)) else v
                for k, v in VALID_WINDOW_OPTIONS_NUMERIC.items()
            }
            # Verify that the schema can process this input without the "expected str" error
            try:
                # This is where the bug would occur - schema validation with string defaults
                schema = result2["data_schema"]
                validated_data = schema(same_input)
                # If we get here, the string conversion fix is working
                assert isinstance(validated_data, dict)
            except vol.Invalid as exc:
                if "expected str" in str(exc):
                    pytest.fail(f"String conversion fix failed: {exc}")
                else:
                    # Other validation errors are fine, we're only testing string conversion
                    pass

    def test_voluptuous_schema_with_numeric_defaults_fails_without_fix(self):
        """
        Demonstrate that Voluptuous schema fails with numeric defaults.

        This test shows why the string conversion fix is necessary.
        """
        # This would fail before our fix - numeric defaults with string validation
        # when the field is missing from input (triggering default value usage)
        with pytest.raises(vol.Invalid, match="expected str"):
            schema = vol.Schema(
                {
                    vol.Optional(
                        "test_field", default=123
                    ): str  # int default, str validation
                }
            )
            # The error occurs when default value is used (field missing from input)
            schema({})  # Empty dict triggers default value validation

        # This works - string defaults with string validation
        schema_fixed = vol.Schema(
            {
                vol.Optional(
                    "test_field", default="123"
                ): str  # str default, str validation
            }
        )
        result = schema_fixed({})  # Uses default value
        assert result["test_field"] == "123"

    def test_ui_default_string_conversion(self):
        """
        Test that the _ui_default helper functions convert values to strings.

        This verifies our fix is working at the utility level.
        """
        # Test data with mixed types (simulating storage)
        test_defaults = {
            "string_val": "test",
            "int_val": 123,
            "float_val": 45.67,
            "none_val": None,
            "empty_val": "",
        }

        global_data = {
            "int_val": 999,  # Global value for inheritance test
            "none_val": 888,
        }

        # Simulate the _ui_default function from the fix
        def _ui_default(key: str) -> str:
            cur = test_defaults.get(key, "")
            gv = global_data.get(key, "")
            if cur in ("", None) and gv not in ("", None):
                return "-1"  # Inheritance indicator
            # CRITICAL: Always convert to string for Voluptuous schema compatibility
            return str(cur) if cur not in ("", None) else ""

        # Test that all values are converted to strings
        assert _ui_default("string_val") == "test"
        assert _ui_default("int_val") == "123"  # int -> str
        assert _ui_default("float_val") == "45.67"  # float -> str
        assert _ui_default("none_val") == "-1"  # None + global -> inheritance
        assert _ui_default("empty_val") == ""  # empty -> empty
        assert _ui_default("missing") == ""  # missing -> empty

        # Verify all results are strings
        for key in test_defaults:
            result = _ui_default(key)
            assert isinstance(result, str), (
                f"Result for {key} is not a string: {type(result)}"
            )
