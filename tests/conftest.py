"""Pytest configuration for Solar Window System tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Add the custom_components directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock homeassistant modules if not available
try:
    import homeassistant
except ImportError:
    # Create mock modules for homeassistant
    sys.modules['homeassistant'] = MagicMock()
    sys.modules['homeassistant.const'] = MagicMock()
    sys.modules['homeassistant.config_entries'] = MagicMock()
    sys.modules['homeassistant.core'] = MagicMock()
    sys.modules['homeassistant.helpers'] = MagicMock()
    sys.modules['homeassistant.helpers.entity'] = MagicMock()
    sys.modules['homeassistant.helpers.update_coordinator'] = MagicMock()
    sys.modules['homeassistant.helpers.storage'] = MagicMock()
    sys.modules['homeassistant.components'] = MagicMock()
    sys.modules['homeassistant.components.sensor'] = MagicMock()
    sys.modules['homeassistant.components.binary_sensor'] = MagicMock()

    # Add Platform enum
    from enum import Enum
    class Platform(Enum):
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"

    sys.modules['homeassistant.const'].Platform = Platform

    # Add Store mock for storage
    class MockStore:
        def __init__(self, hass, version, key):
            self.hass = hass
            self.version = version
            self.key = key

        async def async_load(self):
            return None

        async def async_save(self, data):
            pass

    sys.modules['homeassistant.helpers.storage'].Store = MockStore

    # Add DataUpdateCoordinator mock
    class MockDataUpdateCoordinator:
        def __init__(self, hass, logger, name, update_interval):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.data = {}

        async def async_config_entry_first_refresh(self):
            pass

        async def async_refresh(self):
            pass

    sys.modules['homeassistant.helpers.update_coordinator'].DataUpdateCoordinator = MockDataUpdateCoordinator


@pytest.fixture
def hass():
    """Fixture for Home Assistant instance."""
    from homeassistant.core import HomeAssistant
    hass = HomeAssistant()

    # Create a proper states mock that tracks entities
    class MockStates:
        def __init__(self):
            self._states = {}

        def async_set(self, entity_id, state):
            """Set a state for an entity."""
            self._states[entity_id] = state

        def get(self, entity_id):
            """Get a state for an entity, returning None if not found."""
            if entity_id not in self._states:
                return None
            # Return a mock state object with the state attribute
            state_obj = MagicMock()
            state_obj.state = self._states[entity_id]
            return state_obj

    hass.states = MockStates()
    return hass


@pytest.fixture
def store(hass):
    """Fixture for ConfigStore instance."""
    from custom_components.solar_window_system.store import ConfigStore
    return ConfigStore(hass)
