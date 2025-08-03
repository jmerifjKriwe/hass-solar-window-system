"""Helper functions for testing the solar_window_system integration."""

from collections.abc import Callable
from typing import Any, TypeVar

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from custom_components.solar_window_system.const import DOMAIN

T = TypeVar("T")


async def init_config_flow(hass: HomeAssistant, source: str = "user") -> FlowResult:
    """Initialize a configuration flow for the solar_window_system integration."""
    return await hass.config_entries.flow.async_init(DOMAIN, context={"source": source})


async def init_options_flow(hass: HomeAssistant, entry: ConfigEntry) -> FlowResult:
    """Initialize an options flow for a config entry."""
    return await hass.config_entries.options.async_init(entry.entry_id)


def assert_error_in_step(result: FlowResult, error_field: str) -> None:
    """Assert that a specific error field is present in the flow result."""
    # Use get() for safe TypedDict access
    if result.get("type") != "form":
        pytest.fail("Result type is not 'form'")
    if "errors" not in result:
        pytest.fail("'errors' not found in result")
    errors = result.get("errors", {})
    if errors is not None and error_field not in errors:
        error_msg = f"'{error_field}' not found in errors"
        pytest.fail(error_msg)


def assert_step_id(result: FlowResult, expected_step_id: str) -> None:
    """Assert that the step_id matches the expected value."""
    if result.get("step_id") != expected_step_id:
        pytest.fail("Step ID mismatch")


def assert_result_type(result: FlowResult, expected_type: str) -> None:
    """Assert that the result type matches the expected value."""
    if result.get("type") != expected_type:
        pytest.fail("Result type mismatch")


async def assert_schema_validation_error(
    async_func: Callable[[], Any],
    error_message: str | None = "Schema validation failed",
) -> None:
    """
    Assert that a function raises a schema validation error.

    This is primarily used for Options Flow tests where schema validation errors
    are raised as exceptions rather than returned in the flow result.
    """
    with pytest.raises(Exception, match=error_message) as excinfo:
        await async_func()

    if error_message and error_message not in str(excinfo.value):
        error_msg = f"Error message '{error_message}' not found in exception"
        pytest.fail(error_msg)


async def complete_config_flow_step(
    hass: HomeAssistant, result: FlowResult, user_input: dict[str, Any]
) -> Any:
    """Complete a step in a config flow with the provided user input."""
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )


async def complete_options_flow_step(
    hass: HomeAssistant, result: FlowResult, user_input: dict[str, Any]
) -> Any:
    """Complete a step in an options flow with the provided user input."""
    return await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=user_input
    )


def get_form_schema(result: FlowResult) -> Any:
    """Get the form schema from a flow result if available."""
    return result.get("data_schema")
