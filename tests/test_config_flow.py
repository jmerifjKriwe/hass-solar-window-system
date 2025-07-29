"""Test the config flow for solar_window_system."""
from unittest.mock import patch

import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.solar_window_system.const import DOMAIN
from .mocks import MOCK_USER_INPUT


@pytest.mark.asyncio
async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.solar_window_system.config_flow.SolarWindowConfigFlow._validate_user_input",
        return_value=None,
    ), patch(
        "custom_components.solar_window_system.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Solar Window System"
    assert result2["data"] == MOCK_USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1
