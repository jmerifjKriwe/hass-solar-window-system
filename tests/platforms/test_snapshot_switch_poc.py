"""
PoC snapshot test for a switch entity.

Demonstrates serializing a mapping and a State-like object for a switch.
"""

from unittest.mock import Mock

import pytest

from tests.helpers.serializer import serialize_entity
from tests.helpers.snapshot import assert_matches_snapshot


@pytest.mark.asyncio
async def test_switch_snapshot_minimal() -> None:
    """Serialize a tiny switch and compare to snapshot."""
    raw = {
        "entity_id": "switch.sws_example_outlet",
        "unique_id": "sws_global_example_outlet",
        "state": "on",
        "attributes": {"friendly_name": "Example Outlet"},
    }

    example = serialize_entity(raw, normalize_numbers=True)
    assert_matches_snapshot("switch_snapshot_minimal", example)

    mock_state = Mock()
    mock_state.entity_id = "switch.sws_example_outlet"
    mock_state.state = "on"
    mock_state.attributes = {"friendly_name": "Example Outlet"}
    mock_state.unique_id = "sws_global_example_outlet"

    example2 = serialize_entity(mock_state, normalize_numbers=True)
    if example2 != example:
        msg = "Serializer output for Mock state should match mapping-based output"
        raise AssertionError(msg)
