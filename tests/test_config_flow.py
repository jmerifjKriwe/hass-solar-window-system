from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry


from custom_components.solar_window_system import DOMAIN
from custom_components.solar_window_system.const import CONF_ENTRY_TYPE, DOMAIN


async def test_config_flow_init(hass):
    """Test that the config flow can be initialized."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"


async def test_initial_flow_options(hass):
    """Test that only 'global' is an option on initial setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    # Check that the form presents 'global' as the only option for CONF_ENTRY_TYPE
    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["data_schema"] is not None
    # Assuming CONF_ENTRY_TYPE is the key for the selection
    assert CONF_ENTRY_TYPE in result["data_schema"].schema
    # Check that the 'in' validator contains only 'global'
    assert list(result["data_schema"].schema[CONF_ENTRY_TYPE].container) == ["global"]


@pytest.mark.asyncio
async def test_no_duplicate_global_entry(hass: HomeAssistant):
    """Test that only one 'global' entry can be configured."""

    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_ENTRY_TYPE: "global"},
        title="Solar Window System (Global)",
    )
    existing_entry.add_to_hass(hass)

    # Starte den Flow initial (ohne user_input)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    # Prüfe, dass 'global' nicht in choices ist
    choices = result["data_schema"].schema[CONF_ENTRY_TYPE].container
    assert "global" not in choices

    # Versuche, den Flow mit "window" zu konfigurieren, das ist erlaubt
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ENTRY_TYPE: "window"},
    )
    assert result2["type"] == "form"  # oder was dein Flow für window macht

    # Versuche, den Flow direkt mit "global" zu starten (ohne Formular) - sollte abgelehnt werden
    result3 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_ENTRY_TYPE: "global"},
    )
    assert result3["type"] == "abort"
    assert result3["reason"] == "already_configured"
