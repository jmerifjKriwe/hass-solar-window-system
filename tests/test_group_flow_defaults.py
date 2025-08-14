"""Test that Group config flow shows empty defaults but global suggested values."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN


@pytest.mark.skip(reason="Testen veraltete Logik und müssen noch auf den aktuellen Stand gebracht werden")
@pytest.mark.asyncio
async def test_group_flow_shows_empty_defaults_with_global_suggestions(
    hass: HomeAssistant,
) -> None:
    """When a Global config exists, group form should show empty defaults but suggest global values.

    - Numeric fields: default == "" and description.suggested_value == str(global_value)
    - Sensor selector: default == "-1" and description.suggested_value == sensor entity id
    """
    # Create a Global configuration entry with some values
    global_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Solar Window System",
        data={
            "entry_type": "global_config",
            "diffuse_factor": 0.2,
            "threshold_direct": 250,
            "temperature_indoor_base": 22.0,
            "indoor_temperature_sensor": "sensor.global_temp",
        },
        entry_id="global_config_entry_id",
    )
    global_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(global_entry.entry_id)
    await hass.async_block_till_done()

    # Add the Groups parent entry so the flow offers "Add Group"
    groups_parent_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Group configurations",
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        entry_id="group_parent_entry",
    )
    groups_parent_entry.add_to_hass(hass)

    # Also add the Window parent entry so the integration does not auto-create missing parents
    window_parent_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Window configurations",
        data={"entry_type": "window_configs", "is_subentry_parent": True},
        entry_id="window_parent_entry",
    )
    window_parent_entry.add_to_hass(hass)

    # Patch the temperature sensor helper to return an option list
    with patch(
        "custom_components.solar_window_system.helpers.get_temperature_sensor_entities",
        return_value=[{"value": "sensor.global_temp", "label": "Global Temp"}],
    ):
        # Start the group subentry flow directly so we get the Group add form
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "group_subentry"}
        )
        # Debug: if flow aborted, print the result to help diagnose why
        if result.get("type") == "abort":
            print("FLOW INIT ABORTED:", result)
        assert result["type"] == FlowResultType.FORM

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"entry_type": "group"}
        )
        assert result2["type"] == FlowResultType.FORM

        # Inspect the schema for the group basic page
        schema = result2["data_schema"].schema

        # Numeric fields should have empty default but suggested_value from global
        for key, expected in (
            ("diffuse_factor", "0.2"),
            ("threshold_direct", "250"),
            ("temperature_indoor_base", "22.0"),
        ):
            field = schema[key]
            # default should be empty string
            assert getattr(field, "default", "") in ("", None, "")
            # suggested_value should show the global value (stringified)
            assert field.description["suggested_value"] == expected

        # Sensor selector: default '-1' to indicate inherit, suggested_value is sensor id
        sensor_field = schema["indoor_temperature_sensor"]
        assert getattr(sensor_field, "default", None) == "-1"
        assert sensor_field.description["suggested_value"] == "sensor.global_temp"
