"""Tests for the configuration inheritance logic of Solar Window System."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import (
    INVALID_GLOBAL_BASIC,
    VALID_GLOBAL_BASIC,
    VALID_GLOBAL_ENHANCED,
    VALID_GLOBAL_SCENARIOS,
)


@pytest.fixture
def group_configs_entry(hass: HomeAssistant) -> MockConfigEntry:
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
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Window configurations",
        data={"entry_type": "window_configs", "is_subentry_parent": True},
        entry_id="window_configs_entry_id",
    )
    entry.add_to_hass(hass)
    return entry


async def test_full_global_config_flow_happy_path(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_basic"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], VALID_GLOBAL_BASIC
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_enhanced"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], VALID_GLOBAL_ENHANCED
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_scenarios"

    with patch(
        "custom_components.solar_window_system.config_flow.SolarWindowSystemConfigFlow._create_entries"
    ) as mock_create_entries:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_GLOBAL_SCENARIOS
        )
        await hass.async_block_till_done()

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Solar Window System"

        data = result["data"]
        assert data["window_width"] == 1.5
        assert data["g_value"] == 0.6
        assert data["scenario_b_temp_indoor"] == 24.0
        assert data["entry_type"] == "global_config"

        mock_create_entries.assert_called_once()


async def test_global_config_flow_validation(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_basic"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], INVALID_GLOBAL_BASIC
    )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "global_basic"
    assert result["errors"] is not None
    assert "window_width" in result["errors"]
    assert result["errors"]["window_width"] == "invalid_number"
