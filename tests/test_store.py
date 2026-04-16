"""Tests for the ConfigStore class."""

from unittest.mock import patch

import pytest

from custom_components.solar_window_system.const import (
    CONF_GLOBAL,
    CONF_GROUPS,
    CONF_IRRADIANCE_SENSOR,
    CONF_SENSORS,
    CONF_WINDOWS,
    STORAGE_VERSION,
)


async def test_store_initialization(store):
    """Test store initializes correctly."""
    assert store is not None
    assert store.version == STORAGE_VERSION


@pytest.mark.asyncio
async def test_load_empty_config(hass, store):
    """Test loading overrides when no data exists."""
    from custom_components.solar_window_system.const import CONF_OVERRIDES

    # Mock the Store's async_load to return None (empty storage)
    with patch.object(store._store, "async_load", return_value=None):
        data = await store.async_load()

        # Verify empty overrides structure (store only handles overrides, not config)
        assert data is not None
        assert data["version"] == STORAGE_VERSION
        assert data[CONF_OVERRIDES] == {}


@pytest.mark.asyncio
async def test_save_and_load_config(hass, store):
    """Test saving and loading configuration."""
    test_config = {
        "version": STORAGE_VERSION,
        CONF_GLOBAL: {CONF_SENSORS: {CONF_IRRADIANCE_SENSOR: "sensor.test_irradiance"}},
        CONF_GROUPS: {},
        CONF_WINDOWS: {},
    }

    # Save the config
    await store.async_save(test_config)

    # Load it back
    with patch.object(store._store, "async_load", return_value=test_config):
        loaded_config = await store.async_load()

        # Verify the irradiance sensor value matches
        assert (
            loaded_config[CONF_GLOBAL][CONF_SENSORS][CONF_IRRADIANCE_SENSOR]
            == "sensor.test_irradiance"
        )
