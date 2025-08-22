"""Tests for the configuration inheritance logic of Solar Window System."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch, PropertyMock, AsyncMock

import pytest
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system import config_flow
from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import (
    VALID_GLOBAL_BASIC,
    VALID_GLOBAL_ENHANCED,
    VALID_GLOBAL_SCENARIOS,
    INVALID_GLOBAL_BASIC,
)


@pytest.fixture
def group_configs_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a registered group configs parent entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Group configurations",
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        entry_id="group_configs_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def window_configs_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a registered window configs parent entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Window configurations",
        data={"entry_type": "window_configs", "is_subentry_parent": True},
        entry_id="window_configs_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


# --- Tests for Config Flows (Setup & Validation) ---


async def test_full_global_config_flow_happy_path(hass: HomeAssistant) -> None:
    """Test the full multi-step global configuration flow with valid data."""
    # 1. Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_basic"

    # 2. Provide basic global config
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], VALID_GLOBAL_BASIC
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_enhanced"

    # 3. Provide enhanced global config
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], VALID_GLOBAL_ENHANCED
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_scenarios"

    # 4. Provide scenario config and finalize
    # Mock the creation of sub-entries to isolate the global flow logic
    with patch(
        "custom_components.solar_window_system.config_flow.SolarWindowSystemConfigFlow._create_entries"
    ) as mock_create_entries:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_GLOBAL_SCENARIOS
        )
        await hass.async_block_till_done()

        # 5. Assert the flow is done and a config entry is created
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Solar Window System"

        # 6. Check the data in the created entry
        data = result["data"]
        assert data["window_width"] == 1.5
        assert data["g_value"] == 0.6
        assert data["scenario_b_temp_indoor"] == 24.0
        assert data["entry_type"] == "global_config"

        # Assert that the helper for creating sub-entries was called
        mock_create_entries.assert_called_once()


async def test_global_config_flow_validation(hass: HomeAssistant) -> None:
    """Test validation in the global configuration flow."""
    # 1. Start the config flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_basic"

    # 2. Provide invalid basic global config
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], INVALID_GLOBAL_BASIC
    )

    # 3. Assert that the flow shows a form again with an error
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_basic"
    assert result["errors"] is not None
    assert "window_width" in result["errors"]
    assert result["errors"]["window_width"] == "invalid_number"


# --- Tests for Inheritance Logic ---


@pytest.fixture
def global_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Return a registered global config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={
            "entry_type": "global_config",
            "window_width": 1.5,
            "window_height": 2.0,
            "shadow_depth": 0.5,
            "shadow_offset": 0.2,
            "g_value": 0.6,
            "frame_width": 0.1,
            "tilt": 90,
            "diffuse_factor": 0.2,
            "threshold_direct": 250,
            "threshold_diffuse": 120,
            "temperature_indoor_base": 22.0,
            "temperature_outdoor_base": 20.0,
        },
        entry_id="global_config_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


async def test_group_inherits_from_global(
    hass: HomeAssistant, global_config_entry: MockConfigEntry
) -> None:
    """Test that a group configuration inherits values from the global config."""
    # 1. Simulate stored data for the group sub-entry
    group_data = {
        "entry_type": "group",
        "name": "Living Room Group",
        "diffuse_factor": 0.3,  # This value is local to the group
        "g_value": 0.5,
        "threshold_direct": "",  # This value should be inherited from global
        "threshold_diffuse": 100,
        "temperature_indoor_base": 21.0,
        "temperature_outdoor_base": 19.0,
        "window_width": 1.5,
        "window_height": 2.0,
        "shadow_depth": 0.5,
        "shadow_offset": 0.2,
        "frame_width": 0.1,
        "tilt": 90,
        "forecast_temperature_sensor": "sensor.dummy",
        "weather_warning_sensor": "input_boolean.dummy",
        "scenario_b_temp_indoor": "",
        "scenario_b_temp_outdoor": "",
        "scenario_c_temp_indoor": "",
        "scenario_c_temp_outdoor": "",
        "scenario_c_temp_forecast": "",
        "scenario_c_start_hour": "",
    }

    # 2. Set up the flow handler and mock the sub-entry
    reconfig_flow = config_flow.GroupSubentryFlowHandler()
    reconfig_flow.hass = hass

    mock_subentry = AsyncMock()
    mock_subentry.data = group_data
    mock_subentry.title = "Living Room Group"

    # 3. Patch the necessary methods and start the reconfigure flow
    with (
        patch.object(
            config_flow.GroupSubentryFlowHandler, "source", new_callable=PropertyMock
        ) as mock_source,
        patch.object(
            reconfig_flow, "_get_reconfigure_subentry", return_value=mock_subentry
        ),
        patch(
            "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities",
            return_value=[],
        ),
    ):
        mock_source.return_value = config_entries.SOURCE_RECONFIGURE
        result = await reconfig_flow.async_step_reconfigure(None)

        # 4. Assert that the flow shows the correct form and step
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        # 5. Check the schema for inherited and overridden values
        schema_dict = result["data_schema"].schema

        # Helper to find the key in the schema dict
        def find_key(key_name):
            for key in schema_dict:
                if (
                    isinstance(key, (vol.Optional, vol.Required))
                    and key.schema == key_name
                ):
                    return key
            return None

        # Check overridden value (local value in group)
        diffuse_factor_key = find_key("diffuse_factor")
        assert diffuse_factor_key is not None
        assert diffuse_factor_key.default() == "0.3"

        # Check inherited value (from global config)
        threshold_direct_key = find_key("threshold_direct")
        assert threshold_direct_key is not None
        assert threshold_direct_key.default() == "-1"


async def test_window_inherits_from_global_when_no_group(
    hass: HomeAssistant, global_config_entry: MockConfigEntry
) -> None:
    """Test that a window with no group inherits from the global config."""
    # 1. Simulate stored data for the window sub-entry
    window_data = {
        "entry_type": "window",
        "name": "Kitchen Window",
        "g_value": 0.7,  # local value
        "tilt": "",  # should inherit from global
        "azimuth": 180,
        "azimuth_min": -90,
        "azimuth_max": 90,
        "elevation_min": 0,
        "elevation_max": 90,
        "window_width": 1.5,
        "window_height": 2.0,
        "shadow_depth": 0.5,
        "shadow_offset": 0.2,
        "frame_width": 0.1,
    }

    # 2. Set up the flow handler and mock the sub-entry
    reconfig_flow = config_flow.WindowSubentryFlowHandler()
    reconfig_flow.hass = hass

    mock_subentry = AsyncMock()
    mock_subentry.data = window_data
    mock_subentry.title = "Kitchen Window"

    # 3. Patch the necessary methods and start the reconfigure flow
    with (
        patch.object(
            config_flow.WindowSubentryFlowHandler, "source", new_callable=PropertyMock
        ) as mock_source,
        patch.object(
            reconfig_flow, "_get_reconfigure_subentry", return_value=mock_subentry
        ),
        patch(
            "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities",
            return_value=[],
        ),
        patch.object(reconfig_flow, "_get_group_subentries", return_value=[]),
    ):
        mock_source.return_value = config_entries.SOURCE_RECONFIGURE
        # We need to start with the 'user' step, as reconfigure calls it
        result = await reconfig_flow.async_step_reconfigure(None)
        # The first step is 'user', which gathers basic info. We need to submit it to get to the 'overrides' step.
        result = await reconfig_flow.async_step_user(
            user_input={
                "name": "Kitchen Window",
                "azimuth": "180",
                "azimuth_min": "-90",
                "azimuth_max": "90",
                "elevation_min": "0",
                "elevation_max": "90",
            }
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "overrides"

        # Now we are on the second page, let's check the schema
        schema_dict = result["data_schema"].schema

        def find_key(key_name):
            for key in schema_dict:
                if (
                    isinstance(key, (vol.Optional, vol.Required))
                    and key.schema == key_name
                ):
                    return key
            return None

        # Check overridden value
        g_value_key = find_key("g_value")
        assert g_value_key is not None
        # Compare as float, not string
        assert float(g_value_key.default()) == 0.7

        # Check inherited value
        tilt_key = find_key("tilt")
        assert tilt_key is not None
        assert tilt_key.default() == "-1"


async def test_window_inherits_from_group(
    hass: HomeAssistant,
    global_config_entry: MockConfigEntry,
    group_configs_entry: MockConfigEntry,
) -> None:
    """Test that a window inherits from its assigned group."""
    # 1. Simulate stored data for the group and window sub-entries
    group_data = {
        "entry_type": "group",
        "name": "Living Room Group",
        "diffuse_factor": 0.35,  # This value should be inherited by the window
    }
    window_data = {
        "entry_type": "window",
        "name": "Living Room Window",
        "linked_group_id": "group_sub_id",
        "diffuse_factor": "",  # This value should be inherited from the group
        "azimuth": 180,
        "azimuth_min": -90,
        "azimuth_max": 90,
        "elevation_min": 0,
        "elevation_max": 90,
    }

    # 2. Set up the flow handler and mock the sub-entry
    reconfig_flow = config_flow.WindowSubentryFlowHandler()
    reconfig_flow.hass = hass

    mock_window_subentry = AsyncMock()
    mock_window_subentry.data = window_data
    mock_window_subentry.title = "Living Room Window"

    # 3. Patch the necessary methods and start the reconfigure flow
    with (
        patch.object(
            config_flow.WindowSubentryFlowHandler, "source", new_callable=PropertyMock
        ) as mock_source,
        patch.object(
            reconfig_flow,
            "_get_reconfigure_subentry",
            return_value=mock_window_subentry,
        ),
        patch(
            "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities",
            return_value=[],
        ),
        patch.object(
            reconfig_flow,
            "_get_group_subentries",
            return_value=[("group_sub_id", "Living Room Group")],
        ),
        patch(
            "custom_components.solar_window_system.config_flow._get_global_data_merged",
            return_value=global_config_entry.data,
        ),
    ):
        # In this test, we also need to patch the group entry itself to get its data
        with patch(
            "homeassistant.config_entries.ConfigEntries.async_get_entry",
            return_value=MockConfigEntry(
                domain=DOMAIN, data=group_data, entry_id="group_sub_id"
            ),
        ):
            mock_source.return_value = config_entries.SOURCE_RECONFIGURE
            result = await reconfig_flow.async_step_reconfigure(None)
            result = await reconfig_flow.async_step_user(
                user_input={
                    "name": "Living Room Window",
                    "azimuth": "180",
                    "azimuth_min": "-90",
                    "azimuth_max": "90",
                    "elevation_min": "0",
                    "elevation_max": "90",
                    "linked_group": "Living Room Group",
                }
            )

            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "overrides"

            schema_dict = result["data_schema"].schema

            def find_key(key_name):
                for key in schema_dict:
                    if (
                        isinstance(key, (vol.Optional, vol.Required))
                        and key.schema == key_name
                    ):
                        return key
                return None

            # Check that the inherited value comes from the group, not global
            diffuse_factor_key = find_key("diffuse_factor")
            assert diffuse_factor_key is not None
            assert (
                diffuse_factor_key.default() == "-1"
            )  # Should inherit from group, which is 0.35, but UI shows -1


async def test_window_inherits_from_global_when_group_is_empty(
    hass: HomeAssistant,
    global_config_entry: MockConfigEntry,
    group_configs_entry: MockConfigEntry,
) -> None:
    """Test window fallback to global config if group value is not set."""
    # 1. Create a group sub-entry with an empty value for diffuse_factor
    group_sub_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room Group",
        data={
            "entry_type": "group",
            "name": "Living Room Group",
            "diffuse_factor": "",
            "g_value": 0.5,
            "threshold_direct": 200,
            "threshold_diffuse": 100,
            "temperature_indoor_base": 21.0,
            "temperature_outdoor_base": 19.0,
            "window_width": 1.5,
            "window_height": 2.0,
            "shadow_depth": 0.5,
            "shadow_offset": 0.2,
            "frame_width": 0.1,
            "tilt": 90,
            "forecast_temperature_sensor": "sensor.dummy",
            "weather_warning_sensor": "binary_sensor.dummy",
            "scenario_b_temp_indoor": "",
            "scenario_b_temp_outdoor": "",
            "scenario_c_temp_indoor": "",
            "scenario_c_temp_outdoor": "",
            "scenario_c_temp_forecast": "",
            "scenario_c_start_hour": "",
        },
        entry_id="group_sub_id",
    )
    # Mock the config entry that contains the subentries
    mock_group_parent_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Group configurations",
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        entry_id="group_configs_entry_id",
    )
    # Manually add the subentries attribute to the mock parent entry
    mock_group_parent_entry.subentries = {"group_sub_id": group_sub_entry}

    # Patch async_entries to return the mock group parent and global config
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_entries",
        return_value=[mock_group_parent_entry, global_config_entry],
    ):
        # 2. Simulate stored data for the window sub-entry
        window_data = {
            "entry_type": "window",
            "name": "Living Room Window",
            "linked_group_id": "group_sub_id",
            # diffuse_factor is missing, should inherit from global (0.2)
            "window_width": 1.5,
            "window_height": 2.0,
            "shadow_depth": 0.5,
            "shadow_offset": 0.2,
            "frame_width": 0.1,
            "tilt": 90,
            "forecast_temperature_sensor": "sensor.dummy",
            "weather_warning_sensor": "input_boolean.dummy",
            "g_value": 0.7,
            "diffuse_factor": "",
            "threshold_direct": 250,
            "threshold_diffuse": 120,
            "temperature_indoor_base": 22.0,
            "temperature_outdoor_base": 20.0,
            "scenario_b_temp_indoor": "",
            "scenario_b_temp_outdoor": "",
            "scenario_c_temp_indoor": "",
            "scenario_c_temp_outdoor": "",
            "scenario_c_temp_forecast": "",
            "scenario_c_start_hour": "",
        }
        reconfig_flow = config_flow.WindowSubentryFlowHandler()
        reconfig_flow.hass = hass

        mock_subentry = AsyncMock()
        mock_subentry.data = window_data
        mock_subentry.title = "Living Room Window"

        with (
            patch.object(
                config_flow.WindowSubentryFlowHandler,
                "source",
                new_callable=PropertyMock,
            ) as mock_source,
            patch.object(
                reconfig_flow, "_get_reconfigure_subentry", return_value=mock_subentry
            ),
            patch(
                "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities",
                return_value=[],
            ),
            patch.object(
                reconfig_flow,
                "_get_group_subentries",
                return_value=[("group_sub_id", "Living Room Group")],
            ),
            patch(
                "custom_components.solar_window_system.config_flow._get_global_data_merged",
                return_value=global_config_entry.data,
            ),
        ):
            mock_source.return_value = config_entries.SOURCE_RECONFIGURE
            # Start reconfigure flow
            result = await reconfig_flow.async_step_reconfigure(None)
            # Submit user step to get to overrides
            result = await reconfig_flow.async_step_user(
                user_input={
                    "name": "Living Room Window",
                    "azimuth": "180",
                    "azimuth_min": "-90",
                    "azimuth_max": "90",
                    "elevation_min": "0",
                    "elevation_max": "90",
                    "linked_group": "Living Room Group",
                }
            )
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "overrides"
            schema_dict = result["data_schema"].schema

            def find_key(key_name):
                for key in schema_dict:
                    if (
                        isinstance(key, (vol.Optional, vol.Required))
                        and key.schema == key_name
                    ):
                        return key
                return None

            diffuse_factor_key = find_key("diffuse_factor")
            assert diffuse_factor_key is not None
            # Should inherit from global (0.2), so default is "-1" (inherit), suggested_value is 0.2
            assert diffuse_factor_key.default() == "-1"


async def test_window_overrides_inheritance(
    hass: HomeAssistant,
    global_config_entry: MockConfigEntry,
    group_configs_entry: MockConfigEntry,
) -> None:
    """Test that a window's own value overrides any inherited values."""
    # 1. Create a group sub-entry with a specific value
    group_sub_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room Group",
        data={
            "entry_type": "group",
            "name": "Living Room Group",
            "g_value": 0.5,
            "diffuse_factor": 0.3,
            "threshold_direct": 200,
            "threshold_diffuse": 100,
            "temperature_indoor_base": 21.0,
            "temperature_outdoor_base": 19.0,
            "window_width": 1.5,
            "window_height": 2.0,
            "shadow_depth": 0.5,
            "shadow_offset": 0.2,
            "frame_width": 0.1,
            "tilt": 90,
            "forecast_temperature_sensor": "sensor.dummy",
            "weather_warning_sensor": "input_boolean.dummy",
            "scenario_b_temp_indoor": "",
            "scenario_b_temp_outdoor": "",
            "scenario_c_temp_indoor": "",
            "scenario_c_temp_outdoor": "",
            "scenario_c_temp_forecast": "",
            "scenario_c_start_hour": "",
        },
        entry_id="group_sub_id",
    )
    # Mock the config entry that contains the subentries
    mock_group_parent_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Group configurations",
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        entry_id="group_configs_entry_id",
    )
    # Manually add the subentries attribute to the mock parent entry
    mock_group_parent_entry.subentries = {"group_sub_id": group_sub_entry}

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_entries",
        return_value=[mock_group_parent_entry, global_config_entry],
    ):
        # 2. Simulate stored data for the window sub-entry
        window_data = {
            "entry_type": "window",
            "name": "Living Room Window",
            "linked_group_id": "group_sub_id",
            "g_value": 0.75,  # This should take precedence over group (0.5) and global (0.6)
            "diffuse_factor": 0.2,
            "threshold_direct": 250,
            "threshold_diffuse": 120,
            "temperature_indoor_base": 22.0,
            "temperature_outdoor_base": 20.0,
            "window_width": 1.5,
            "window_height": 2.0,
            "shadow_depth": 0.5,
            "shadow_offset": 0.2,
            "frame_width": 0.1,
            "tilt": 90,
            "forecast_temperature_sensor": "sensor.dummy",
            "weather_warning_sensor": "input_boolean.dummy",
            "scenario_b_temp_indoor": "",
            "scenario_b_temp_outdoor": "",
            "scenario_c_temp_indoor": "",
            "scenario_c_temp_outdoor": "",
            "scenario_c_temp_forecast": "",
            "scenario_c_start_hour": "",
        }
        reconfig_flow = config_flow.WindowSubentryFlowHandler()
        reconfig_flow.hass = hass

        mock_subentry = AsyncMock()
        mock_subentry.data = window_data
        mock_subentry.title = "Living Room Window"

        with (
            patch.object(
                config_flow.WindowSubentryFlowHandler,
                "source",
                new_callable=PropertyMock,
            ) as mock_source,
            patch.object(
                reconfig_flow, "_get_reconfigure_subentry", return_value=mock_subentry
            ),
            patch(
                "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities",
                return_value=[],
            ),
            patch.object(
                reconfig_flow,
                "_get_group_subentries",
                return_value=[("group_sub_id", "Living Room Group")],
            ),
            patch(
                "custom_components.solar_window_system.config_flow._get_global_data_merged",
                return_value=global_config_entry.data,
            ),
        ):
            mock_source.return_value = config_entries.SOURCE_RECONFIGURE
            # Start reconfigure flow
            result = await reconfig_flow.async_step_reconfigure(None)
            # Submit user step to get to overrides
            result = await reconfig_flow.async_step_user(
                user_input={
                    "name": "Living Room Window",
                    "azimuth": "180",
                    "azimuth_min": "-90",
                    "azimuth_max": "90",
                    "elevation_min": "0",
                    "elevation_max": "90",
                    "linked_group": "Living Room Group",
                }
            )
            assert result["type"] == FlowResultType.FORM
            assert result["step_id"] == "overrides"
            schema_dict = result["data_schema"].schema

            def find_key(key_name):
                for key in schema_dict:
                    if (
                        isinstance(key, (vol.Optional, vol.Required))
                        and key.schema == key_name
                    ):
                        return key
                return None

            g_value_key = find_key("g_value")
            assert g_value_key is not None
            # Should use window's own value (0.75)
            assert float(g_value_key.default()) == 0.75
