"""Tests for duplicate-name handling in Group SubentryFlowHandler."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from unittest.mock import PropertyMock, patch
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.data_entry_flow import FlowResultType

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import VALID_GROUP_OPTIONS_NUMERIC


if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_create_group_duplicate_name(hass: HomeAssistant) -> None:
    """Creating a group with a duplicate name should produce an error."""
    # Create parent entry representing the groups container
    group_parent_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        title="Group configurations",
    )
    group_parent_entry.add_to_hass(hass)

    # First creation should succeed
    handler1 = __import__(
        "custom_components.solar_window_system.config_flow",
        fromlist=["GroupSubentryFlowHandler"],
    ).GroupSubentryFlowHandler()
    handler1.hass = hass
    handler1.parent_entry = group_parent_entry  # type: ignore[attr-defined]
    with patch.object(
        type(handler1), "source", new_callable=PropertyMock, return_value="user"
    ):
        group_config = {
            k: v for k, v in VALID_GROUP_OPTIONS_NUMERIC.items() if k != "name"
        }
        result1 = await handler1.async_step_user(
            {"name": "My Test Group", **group_config}
        )
        result1 = await handler1.async_step_enhanced({})
        assert result1["type"] == FlowResultType.CREATE_ENTRY

    # Simulate existing subentry to provoke duplicate-name error
    class DummySub:
        def __init__(self, title: str) -> None:
            self.title = title
            self.subentry_type = "group"
            self.data = {"name": title}

    fake_subentries = {"1": DummySub("My Test Group")}
    # Attach a constant subentries mapping to simulate existing child entries
    group_parent_entry.subentries = fake_subentries  # type: ignore[attr-defined]

    # Second creation with same name should return a form with errors
    handler2 = __import__(
        "custom_components.solar_window_system.config_flow",
        fromlist=["GroupSubentryFlowHandler"],
    ).GroupSubentryFlowHandler()
    handler2.hass = hass
    handler2.parent_entry = group_parent_entry  # type: ignore[attr-defined]
    with patch.object(
        type(handler2), "source", new_callable=PropertyMock, return_value="subentry"
    ):
        group_config = {
            k: v for k, v in VALID_GROUP_OPTIONS_NUMERIC.items() if k != "name"
        }
        result2 = await handler2.async_step_user(
            {"name": "My Test Group", **group_config}
        )
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"name": "duplicate_name"}
