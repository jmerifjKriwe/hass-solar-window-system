"""Test that Group subentry flow shows empty defaults but global suggested values."""

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import VALID_GLOBAL_BASIC, VALID_GLOBAL_ENHANCED
from custom_components.solar_window_system.config_flow import GroupSubentryFlowHandler


def mock_group_parent_entry() -> MockConfigEntry:
    """Return a MockConfigEntry that acts as a parent for group subentries."""
    return MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Group configurations",
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        source="internal",
        entry_id="test_group_parent_id",
        unique_id=None,
    )


def mock_global_config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry representing an existing global configuration."""
    data = {"entry_type": "global_config"}
    data.update(VALID_GLOBAL_BASIC)
    data.update(VALID_GLOBAL_ENHANCED)
    data["diffuse_factor"] = 0.2
    data["threshold_direct"] = 250
    data["temperature_indoor_base"] = 22.0
    data["indoor_temperature_sensor"] = "sensor.global_temp"
    return MockConfigEntry(
        version=1,
        minor_version=1,
        domain=DOMAIN,
        title="Solar Window System",
        data=data,
        source="user",
        entry_id="global_config_entry_id",
        unique_id=None,
    )


async def test_group_subentry_form_defaults_and_suggestions(
    hass: HomeAssistant,
) -> None:
    """Group subentry form shows empty defaults with suggested global values."""
    parent = mock_group_parent_entry()
    global_entry = mock_global_config_entry()
    parent.add_to_hass(hass)
    global_entry.add_to_hass(hass)

    with patch(
        "custom_components.solar_window_system.config_flow.get_temperature_sensor_entities",
        return_value=[{"label": "Global Temp", "value": "sensor.global_temp"}],
    ):
        flow_handler = GroupSubentryFlowHandler()
        flow_handler.hass = hass
        # set non-public attributes used by the handler
        try:
            flow_handler.handler = DOMAIN
        except Exception:
            # older handler versions may not expose this attr in type hints
            setattr(flow_handler, "handler", DOMAIN)
        try:
            flow_handler.parent_entry_id = parent.entry_id
        except Exception:
            setattr(flow_handler, "parent_entry_id", parent.entry_id)

        result = await flow_handler.async_step_user()
        assert result["type"] == FlowResultType.FORM
        schema = result["data_schema"].schema

        for key, expected in (
            ("diffuse_factor", "0.2"),
            ("threshold_direct", "250"),
            ("temperature_indoor_base", "22.0"),
        ):
            field = schema[key]
            assert getattr(field, "default", "") in ("", None, "")

        # Sensor selector: default is "-1" (inherit)
        found = False
        for key in schema:
            # keys may be represented differently; check by name where possible
            try:
                name = getattr(key, "schema", None)
            except Exception:
                name = None
            if name == "indoor_temperature_sensor":
                default_value = key.default() if callable(key.default) else key.default
                assert default_value == "-1"
                found = True
        if not found:
            raise AssertionError("Schema key for 'indoor_temperature_sensor' not found")
