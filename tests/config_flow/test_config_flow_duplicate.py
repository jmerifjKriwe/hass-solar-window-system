"""Test that creating entities with duplicate names is not allowed via subentry flows."""

from unittest.mock import PropertyMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.solar_window_system.const import DOMAIN
from tests.test_data import VALID_GROUP_OPTIONS_NUMERIC


@pytest.mark.asyncio
async def test_create_group_duplicate_name(hass: HomeAssistant) -> None:
    """Test that creating a group with a duplicate name shows an error (subentry flow handler)."""
    # Set up the group parent entry (simulate what config flow would do)
    group_parent_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"entry_type": "group_configs", "is_subentry_parent": True},
        title="Group configurations",
    )
    group_parent_entry.add_to_hass(hass)

    # Create the first group via handler, patching source property to 'user' for creation
    handler1 = __import__(
        "custom_components.solar_window_system.config_flow",
        fromlist=["GroupSubentryFlowHandler"],
    ).GroupSubentryFlowHandler()
    handler1.hass = hass
    handler1.parent_entry = group_parent_entry
    with patch.object(
        type(handler1), "source", new_callable=PropertyMock, return_value="user"
    ):
        # Step 1: user
        group_config = {
            k: v for k, v in VALID_GROUP_OPTIONS_NUMERIC.items() if k != "name"
        }
        result1 = await handler1.async_step_user(
            {"name": "My Test Group", **group_config}
        )
        # Step 2: enhanced
        result1 = await handler1.async_step_enhanced({})
        assert result1["type"] == FlowResultType.CREATE_ENTRY

    # Patch subentries to simulate an existing group
    class DummySub:
        def __init__(self, title: str) -> None:
            self.title = title
            self.subentry_type = "group"
            self.data = {"name": title}

    fake_subentries = {"1": DummySub("My Test Group")}
    # Dynamically add a subentries property to the group_parent_entry instance
    group_parent_entry.subentries = property(lambda self: fake_subentries).__get__(
        group_parent_entry, type(group_parent_entry)
    )
    # Try to create a second group with the same name
    handler2 = __import__(
        "custom_components.solar_window_system.config_flow",
        fromlist=["GroupSubentryFlowHandler"],
    ).GroupSubentryFlowHandler()
    handler2.hass = hass
    handler2.parent_entry = group_parent_entry
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
