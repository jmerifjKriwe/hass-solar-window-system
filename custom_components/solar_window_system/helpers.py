"""Shared helpers for Solar Window System custom component."""

from homeassistant.helpers import entity_registry as er
from typing import Any


async def get_temperature_sensor_entities(hass: Any) -> list[str]:
    """Collect temperature sensor entity_ids to present as options."""
    entity_registry = er.async_get(hass)
    temperature_entities: list[str] = []
    for ent in entity_registry.entities.values():
        if (
            ent.entity_id.startswith("sensor.")
            and not ent.disabled_by
            and not ent.hidden_by
        ):
            state = hass.states.get(ent.entity_id)
            if state and state.attributes.get("unit_of_measurement") in (
                "°C",
                "°F",
                "K",
            ):
                temperature_entities.append(ent.entity_id)
    return temperature_entities
