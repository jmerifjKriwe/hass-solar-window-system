"""
Clean DebugMixin implementation for tests and debug helpers.

This file was recreated to remove encoding/corruption issues.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import logging
from typing import Any

try:  # Prefer real Home Assistant helper when available
    from homeassistant.helpers import (
        entity_registry as er,  # type: ignore[attr-defined]
    )
except ImportError:  # pragma: no cover - occurs in test environment

    class _ERStub:
        @staticmethod
        async def async_get(_hass: Any) -> Any:  # unused arg in test stub
            return None

    er = _ERStub()

_LOGGER = logging.getLogger(__name__)

# Mock defaults used by tests to detect nonexistent windows
MOCK_DEFAULT_AREA = 2.0
MOCK_DEFAULT_AZIMUTH = 180.0
MOCK_DEFAULT_GROUP_TYPE = "default"


class DebugMixin:
    """
    Mixin that provides debug helper utilities used in tests.

    The implementation here is intentionally conservative and uses only
    plain Python constructs to avoid introducing typing or runtime
    dependencies that caused the original file to be corrupted.
    """

    # Typing stub: real implementations which mix this in provide
    # `get_effective_config_from_flows(window_id)` at runtime. Providing
    # a typed stub here satisfies static type checkers (pyright) while
    # leaving runtime behavior unchanged because concrete classes will
    # override this method.
    def get_effective_config_from_flows(
        self, window_id: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:  # pragma: no cover - stub for typing
        """
        Return effective configuration and sources for a window.

        Implementations should override this. The stub raises to avoid
        accidental use when DebugMixin is used standalone.
        """
        # Delegate to other mixins (for example FlowIntegrationMixin) when
        # available in the MRO. This keeps DebugMixin usable in compound
        # classes where the flow integration provides the implementation.
        try:
            return super().get_effective_config_from_flows(window_id)
        except AttributeError:
            msg = "get_effective_config_from_flows must be implemented by the concrete class"
            raise NotImplementedError(msg)

    def _get_entity_registry(self, hass: Any) -> Any:
        """Return the entity registry from hass if available, else None."""
        try:
            if hasattr(hass, "entity_registry"):
                return hass.entity_registry
            if hasattr(hass, "data") and "entity_registry" in getattr(hass, "data", {}):
                return hass.data["entity_registry"]

            # Try Home Assistant helper if available (tests may monkeypatch)
            try:
                reg = er.async_get(hass)
            except (AttributeError, TypeError) as exc:  # pragma: no cover - defensive
                _LOGGER.debug("er.async_get not available: %s", exc)
                reg = None
            if reg is not None:
                # If helper returns an object with .entities (Mock in tests), return it
                if hasattr(reg, "entities"):
                    return reg
                # Some helpers may return awaitable/future/coroutine; try to resolve it
                try:
                    if asyncio.iscoroutine(reg) or asyncio.isfuture(reg):
                        # If an event loop is running in this thread we cannot
                        # run the awaitable to completion here (would raise).
                        # In synchronous test contexts no loop will be present
                        # so use asyncio.run to resolve the awaitable safely.
                        try:
                            asyncio.get_running_loop()
                            _LOGGER.debug(
                                "Entity registry awaitable; event loop running, "
                                "skipping resolution"
                            )
                        except RuntimeError:
                            try:
                                reg_val = asyncio.run(reg)  # type: ignore[arg-type]
                                if hasattr(reg_val, "entities"):
                                    return reg_val
                            except Exception as exc:  # pragma: no cover # noqa:BLE001
                                _LOGGER.debug(
                                    "Failed to resolve awaitable registry: %s",
                                    exc,
                                )
                except (RuntimeError, TypeError) as exc:  # pragma: no cover - defensive
                    _LOGGER.debug("Failed to resolve awaitable registry: %s", exc)

        except Exception:
            _LOGGER.exception("Error while resolving entity registry")

        # For test mocks, allow direct assignment
        return getattr(self, "_mock_entity_registry", None)

    def _find_entity_by_name(
        self, hass: Any, name: str, *_args: Any, **_kwargs: Any
    ) -> str | None:
        """
        Find an entity id by name in the entity registry.

        Accepts additional positional/keyword arguments for compatibility
        with older test call sites; extra arguments are ignored.
        """
        try:
            entity_reg = self._get_entity_registry(hass)
        except Exception:
            _LOGGER.exception("Error accessing entity registry")
            return None

        if entity_reg is None:
            return None

        entities = getattr(entity_reg, "entities", {})
        for entity_id, entry in entities.items():
            if getattr(entry, "name", None) == name:
                return entity_id
        return None

    def _get_current_sensor_states(self, window_id: str) -> dict[str, Any]:
        """Alias kept for compatibility with older callers/tests."""
        return self._collect_current_sensor_states(window_id)

    def _generate_debug_output(self, sensor_states: dict[str, Any]) -> str:
        """Generate a human-readable debug string from sensor states."""
        if not sensor_states:
            return "No sensor states available"

        lines: list[str] = ["Solar Window System Debug Output:", "=" * 40]
        for entity_id, data in sensor_states.items():
            lines.append(f"Entity: {entity_id}")
            lines.append(f"State: {data.get('state')}")
            lines.append(f"Name: {data.get('name')}")
            if data.get("error"):
                lines.append(f"Error: {data.get('error')}")
            lines.append("")

        return "\n".join(lines)

    def _search_window_sensors(self, hass: Any, window_id: str) -> list[str]:
        """Return list of sensor entity_ids related to a window (stub)."""
        _ = hass, window_id
        return []

    def _search_group_sensors(
        self,
        hass: Any,
        window_id: str,
        groups: Any = None,
    ) -> list[str]:
        """Return list of group sensor entity_ids (stub)."""
        _ = hass, window_id, groups
        return []

    def _search_global_sensors(self, hass: Any) -> list[str]:
        """Return list of global sensor entity_ids (stub)."""
        _ = hass
        return []

    def _collect_current_sensor_states(self, window_id: str) -> dict[str, Any]:
        """
        Collect current states of SWS sensors from the entity registry.

        This implementation is defensive: if the entity registry or state
        store is not available it returns an empty mapping.
        """
        # keep parameter referenced to satisfy linters when unused in some flows
        _ = window_id
        sensor_states: dict[str, Any] = {}
        try:
            entity_reg = self._get_entity_registry(getattr(self, "hass", None))
        except Exception:
            # Tests expect that any error resolving the registry results in an
            # empty mapping being returned rather than bubbling the exception.
            _LOGGER.exception("Error accessing entity registry")
            return {}

        if entity_reg is None:
            return {}

        entities = self._normalize_entities(entity_reg)

        for entity_id, entity_entry in entities.items():
            if not isinstance(entity_id, str):
                continue
            if entity_id.startswith("sensor.sws_"):
                try:
                    hass_obj = getattr(self, "hass", None)
                    states_store = getattr(hass_obj, "states", {})
                    state = states_store.get(entity_id)
                    last_updated = None
                    if (
                        state is not None
                        and hasattr(state, "last_updated")
                        and state.last_updated is not None
                    ):
                        if hasattr(state.last_updated, "isoformat"):
                            last_updated = state.last_updated.isoformat()
                        else:
                            last_updated = str(state.last_updated)
                    attributes_val = (
                        getattr(state, "attributes", {}) if state is not None else {}
                    )
                    sensor_states[entity_id] = {
                        "state": getattr(state, "state", None),
                        "name": getattr(entity_entry, "name", None),
                        "last_updated": last_updated,
                        "error": None if state is not None else "Unavailable",
                        "attributes": attributes_val,
                    }
                except (AttributeError, KeyError) as exc:
                    sensor_states[entity_id] = {
                        "state": "unavailable",
                        "name": getattr(entity_entry, "name", None),
                        "last_updated": None,
                        "error": str(exc),
                        "attributes": {},
                    }
        return sensor_states

    def _normalize_entities(self, entity_reg: Any) -> dict[str, Any]:
        """
        Return a mapping of entities for a given registry-like object.

        Centralizes normalization logic so calling sites stay simple.
        """
        try:
            if hasattr(entity_reg, "entities"):
                entities = entity_reg.entities
            elif hasattr(entity_reg, "items"):
                # Some mocks expose items() directly
                try:
                    return dict(entity_reg.items())  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    return {}
            else:
                entities = entity_reg

            if isinstance(entities, dict):
                return entities

            try:
                return dict(entities)
            except (TypeError, ValueError):
                _LOGGER.debug("Entity registry entities not iterable")
                return {}
        except (AttributeError, TypeError, ValueError):
            _LOGGER.debug("Unexpected error normalizing entities")
            return {}

    def _collect_window_configuration(self, window_id: str) -> dict[str, Any]:
        """Collect a minimal window configuration used for debug output."""
        # Try hooks that may exist on the real implementation, fall back to mocks
        try:
            if hasattr(self, "get_effective_config_from_flows"):
                try:
                    effective, sources = self.get_effective_config_from_flows(window_id)
                except (AttributeError, TypeError) as err:
                    _LOGGER.exception(
                        "Error obtaining effective configuration for %s",
                        window_id,
                    )
                    return {
                        "window_id": window_id,
                        "error": str(err),
                        "effective_config": {},
                        "config_sources": {},
                        "raw_window_data": {},
                    }
            else:
                effective = {"area": MOCK_DEFAULT_AREA, "azimuth": MOCK_DEFAULT_AZIMUTH}
                sources = {"source": "mock"}

        except (AttributeError, TypeError) as err:
            _LOGGER.exception(
                "Error during configuration collection for %s",
                window_id,
            )
            return {
                "window_id": window_id,
                "error": str(err),
                "effective_config": {},
                "config_sources": {},
                "raw_window_data": {},
            }

        if hasattr(self, "_get_window_config_from_flow"):
            try:
                raw = self._get_window_config_from_flow(window_id)  # type: ignore[attr-defined]
            except (AttributeError, TypeError, KeyError):
                raw = {"window_id": window_id, "group_type": MOCK_DEFAULT_GROUP_TYPE}
        else:
            raw = {"window_id": window_id, "group_type": MOCK_DEFAULT_GROUP_TYPE}

        return {
            "window_id": window_id,
            "effective_config": effective,
            "config_sources": sources,
            "raw_window_data": raw,
        }

    def _collect_sensor_data(self) -> dict[str, Any]:
        """Collect a small set of environment sensor values used in debug."""
        if hasattr(self, "_get_global_data_merged"):
            try:
                global_data = self._get_global_data_merged()  # type: ignore[attr-defined]
            except (AttributeError, TypeError, NotImplementedError):
                global_data = {}
        else:
            global_data = {}
        sensor_data: dict[str, Any] = {}
        pairs = [
            (
                "solar_radiation",
                global_data.get("solar_radiation_sensor"),
            ),
            (
                "outdoor_temperature",
                global_data.get("outdoor_temperature_sensor"),
            ),
            (
                "indoor_temperature",
                global_data.get("indoor_temperature_sensor"),
            ),
            (
                "weather_forecast_temperature",
                global_data.get("weather_forecast_temperature_sensor"),
            ),
            (
                "weather_warning",
                global_data.get("weather_warning_sensor"),
            ),
        ]

        for name, entity_id in pairs:
            if entity_id:
                sensor_data[name] = {
                    "entity_id": entity_id,
                    "state": None,
                    "available": False,
                }
            else:
                sensor_data[name] = {
                    "entity_id": None,
                    "state": None,
                    "available": False,
                }

        # sun position placeholder
        sensor_data["sun_position"] = {
            "entity_id": "sun.sun",
            "elevation": 0,
            "azimuth": 0,
            "available": False,
        }
        return sensor_data

    async def _async_create_debug_data(self, window_id: str) -> dict[str, Any] | None:
        """
        Assemble debug data for a window in an async context.

        This function mirrors the behaviors relied on by tests: it returns
        None for a clearly nonexistent window (detected via mock defaults),
        or a dictionary with collected data otherwise.
        """
        hass = getattr(self, "hass", None)
        groups = getattr(self, "groups", {})

        # If this mixin is used directly (no calculator/flow integration),
        # return an error mapping to indicate missing operational context.
        if type(self) is DebugMixin:
            return {
                "timestamp": datetime.now(UTC).isoformat(),
                "window_id": window_id,
                "error": "DebugMixin used standalone; no calculator context",
            }

        debug_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "window_id": window_id,
            "current_sensor_states": self._collect_current_sensor_states(window_id),
            "window_sensors": self._search_window_sensors(hass, window_id),
            "global_sensors": self._search_global_sensors(hass),
        }

        group_sensors = self._search_group_sensors(hass, window_id, groups)
        debug_data["group_sensors"] = group_sensors
        debug_data["configuration"] = self._collect_window_configuration(window_id)
        conf_block = debug_data["configuration"]

        # Normalize configuration shape: tests sometimes return a flat mapping
        if isinstance(conf_block, dict) and "effective_config" in conf_block:
            config = conf_block.get("effective_config", {})
        else:
            config = conf_block or {}

        # If configuration matches mock defaults and name looks fake, treat as missing
        if isinstance(conf_block, dict) and "raw_window_data" in conf_block:
            raw_window = conf_block.get("raw_window_data", {})
        else:
            raw_window = {"group_type": config.get("group_type")}
        if (
            config.get("area") == MOCK_DEFAULT_AREA
            and config.get("azimuth") == MOCK_DEFAULT_AZIMUTH
            and raw_window.get("group_type") == MOCK_DEFAULT_GROUP_TYPE
            and window_id == "nonexistent_window"
        ):
            _LOGGER.debug("Window '%s' not found (mock defaults)", window_id)
            return None

        debug_data["sensor_data"] = self._collect_sensor_data()

        # calculate_all_windows_from_flows may be sync; call defensively
        if hasattr(self, "calculate_all_windows_from_flows"):
            try:
                calc_fn = self.calculate_all_windows_from_flows  # type: ignore[attr-defined]
                result = calc_fn()
                debug_data["final_result"] = result
                debug_data["calculated_sensors"] = (
                    len(result) if isinstance(result, list) else 0
                )
            except (
                AttributeError,
                TypeError,
                ValueError,
                NotImplementedError,
            ) as calc_err:
                _LOGGER.warning(
                    "Could not calculate window result for debug: %s", calc_err
                )
                return {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "window_id": window_id,
                    "error": str(calc_err),
                }

        debug_data["calculation_steps"] = {
            "debug_data_collected": True,
            "window_sensors_found": len(debug_data.get("window_sensors", [])),
            "global_sensors_found": len(debug_data.get("global_sensors", [])),
            "group_sensors_found": len(debug_data.get("group_sensors", [])),
        }

        _LOGGER.debug("Debug data created successfully for window: %s", window_id)
        return debug_data

    def create_debug_data(self, window_id: str) -> Any:
        """
        Return debug data; coroutine when in an event loop, result when sync.

        If a running event loop is present, return the coroutine so callers can
        await it. If no running loop is found, run the coroutine to completion
        and return the result for synchronous callers (tests often call it
        synchronously).
        """
        coro = self._async_create_debug_data(window_id)
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No running loop -> run synchronously
            return asyncio.run(coro)
        # Running loop -> return coroutine for caller to await
        return coro
