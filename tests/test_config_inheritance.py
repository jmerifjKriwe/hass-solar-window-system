"""Tests for the configuration inheritance logic of Solar Window System."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch, PropertyMock

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN

# --- Test Data ---

VALID_GLOBAL_BASIC = {
    "window_width": "1.5",
    "window_height": "2.0",
    "shadow_depth": "0.5",
    "shadow_offset": "0.2",
    "solar_radiation_sensor": "sensor.dummy_solar",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor",
    "forecast_temperature_sensor": "sensor.dummy",
    "weather_warning_sensor": "binary_sensor.dummy",
}

VALID_GLOBAL_ENHANCED = {
    "g_value": "0.6",
    "frame_width": "0.1",
    "tilt": "90",
    "diffuse_factor": "0.2",
    "threshold_direct": "250",
    "threshold_diffuse": "120",
    "temperature_indoor_base": "22.0",
    "temperature_outdoor_base": "20.0",
}

VALID_GLOBAL_SCENARIOS = {
    "scenario_b_temp_indoor": "24",
    "scenario_b_temp_outdoor": "26",
    "scenario_c_temp_indoor": "22",
    "scenario_c_temp_outdoor": "25",
    "scenario_c_temp_forecast": "28",
    "scenario_c_start_hour": "8",
}

INVALID_GLOBAL_BASIC = {
    "window_width": "abc",
    "window_height": "2.0",
    "shadow_depth": "0.5",
    "shadow_offset": "0.2",
    "solar_radiation_sensor": "sensor.dummy_solar",
    "outdoor_temperature_sensor": "sensor.dummy_outdoor",
}


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


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
async def test_group_inherits_from_global(
    hass: HomeAssistant, global_config_entry: MockConfigEntry
) -> None:
    """Test that a group configuration inherits values from the global config."""
    # 1. Create a group config entry with some values missing
    group_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room Group",
        data={
            "entry_type": "group",
            "name": "Living Room Group",
            "diffuse_factor": 0.3,
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
            "weather_warning_sensor": "input_boolean.dummy",
            "scenario_b_temp_indoor": "",
            "scenario_b_temp_outdoor": "",
            "scenario_c_temp_indoor": "",
            "scenario_c_temp_outdoor": "",
            "scenario_c_temp_forecast": "",
            "scenario_c_start_hour": "",
        },
        entry_id="group_entry_id",
    )
    group_entry.add_to_hass(hass)

    # 2. Initialize the options flow for the group
    with patch(
        "custom_components.solar_window_system.options_flow.get_temperature_sensor_entities",
        return_value=[],
    ):
        flow = await hass.config_entries.options.async_init(group_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            flow["flow_id"], user_input=None
        )

    # 3. Check the schema for inherited and overridden values
    assert result["type"] == FlowResultType.FORM
    schema = result["data_schema"].schema

    # Check overridden value
    diffuse_factor_field = schema["diffuse_factor"]
    assert diffuse_factor_field.description["suggested_value"] == 0.3

    # Check inherited value
    threshold_direct_field = schema["threshold_direct"]
    assert threshold_direct_field.description["suggested_value"] == 250


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
async def test_window_inherits_from_global_when_no_group(
    hass: HomeAssistant, global_config_entry: MockConfigEntry
) -> None:
    """Test that a window with no group inherits from the global config."""
    # 1. Create a window config entry with no group
    window_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kitchen Window",
        data={
            "entry_type": "window",
            "name": "Kitchen Window",
            "g_value": 0.7,
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
        },
        entry_id="window_entry_id",
    )
    window_entry.add_to_hass(hass)

    # 2. Initialize the options flow for the window
    with patch(
        "custom_components.solar_window_system.options_flow.get_temperature_sensor_entities",
        return_value=[],
    ):
        flow = await hass.config_entries.options.async_init(window_entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            flow["flow_id"], user_input=None
        )

    # 3. Check the schema for inherited and overridden values
    assert result["type"] == FlowResultType.FORM
    schema = result["data_schema"].schema

    # Check overridden value
    g_value_field = schema["g_value"]
    assert g_value_field.description["suggested_value"] == 0.7

    # Check inherited value
    tilt_field = schema["tilt"]
    assert tilt_field.description["suggested_value"] == 90


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
async def test_window_inherits_from_group(
    hass: HomeAssistant,
    global_config_entry: MockConfigEntry,
    group_configs_entry: MockConfigEntry,
) -> None:
    """Test that a window inherits from its assigned group."""
    # 1. Create a group sub-entry with specific values
    group_sub_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room Group",
        data={
            "entry_type": "group",
            "name": "Living Room Group",
            "diffuse_factor": 0.35,
            "g_value": 0.5,
            "threshold_direct": 200,
            "threshold_diffuse": 100,
            "temperature_indoor_base": 21.0,
            "temperature_outdoor_base": 19.0,
            # Add all scenario keys with empty string defaults
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

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_entries",
        return_value=[mock_group_parent_entry, global_config_entry],
    ):
        # 2. Create a window entry linked to the group
        window_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Living Room Window",
            data={
                "entry_type": "window",
                "name": "Living Room Window",
                "linked_group_id": "group_sub_id",
                # diffuse_factor is missing, should inherit from group (0.35)
                "window_width": 1.5,
                "window_height": 2.0,
                "shadow_depth": 0.5,
                "shadow_offset": 0.2,
                "frame_width": 0.1,
                "tilt": 90,
                "forecast_temperature_sensor": "sensor.dummy",
                "weather_warning_sensor": "input_boolean.dummy",
                # Add all scenario keys with empty string defaults
                "scenario_b_temp_indoor": "",
                "scenario_b_temp_outdoor": "",
                "scenario_c_temp_indoor": "",
                "scenario_c_temp_outdoor": "",
                "scenario_c_temp_forecast": "",
                "scenario_c_start_hour": "",
            },
            entry_id="window_entry_id",
        )
        window_entry.add_to_hass(hass)

        # 3. Initialize the options flow for the window
        with patch(
            "custom_components.solar_window_system.options_flow.get_temperature_sensor_entities",
            return_value=[],
        ):
            flow = await hass.config_entries.options.async_init(window_entry.entry_id)
            result = await hass.config_entries.options.async_configure(
                flow["flow_id"], user_input=None
            )

        # 4. Check that the inherited value comes from the group, not global
        assert result["type"] == FlowResultType.FORM
        schema = result["data_schema"].schema
        diffuse_factor_field = schema["diffuse_factor"]
        assert (
            diffuse_factor_field.description["suggested_value"] == 0.35
        )  # Group value, not global 0.2


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
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

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_entries",
        return_value=[mock_group_parent_entry, global_config_entry],
    ):
        # 2. Create a window entry linked to the group
        window_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Living Room Window",
            data={
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
            },
            entry_id="window_entry_id",
        )
        window_entry.add_to_hass(hass)

        # 3. Initialize the options flow for the window
        with patch(
            "custom_components.solar_window_system.options_flow.get_temperature_sensor_entities",
            return_value=[],
        ):
            flow = await hass.config_entries.options.async_init(window_entry.entry_id)
            result = await hass.config_entries.options.async_configure(
                flow["flow_id"], user_input=None
            )

        # 4. Check that the inherited value comes from global, as group is empty
        assert result["type"] == FlowResultType.FORM
        schema = result["data_schema"].schema
        diffuse_factor_field = schema["diffuse_factor"]
        assert (
            diffuse_factor_field.description["suggested_value"] == 0.2
        )  # Global value


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
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
        # 2. Create a window entry with its own value, linked to the group
        window_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Living Room Window",
            data={
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
            },
            entry_id="window_entry_id",
        )
        window_entry.add_to_hass(hass)

        # 3. Initialize the options flow for the window
        with patch(
            "custom_components.solar_window_system.options_flow.get_temperature_sensor_entities",
            return_value=[],
        ):
            flow = await hass.config_entries.options.async_init(window_entry.entry_id)
            result = await hass.config_entries.options.async_configure(
                flow["flow_id"], user_input=None
            )

        # 4. Check that the window's own value is used
        assert result["type"] == FlowResultType.FORM
        schema = result["data_schema"].schema
        g_value_field = schema["g_value"]
        assert (
            g_value_field.description["suggested_value"] == 0.75
        )  # Window's own value
