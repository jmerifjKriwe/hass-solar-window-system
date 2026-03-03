"""Pytest configuration for Solar Window System tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

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
    sys.modules['homeassistant.components'] = MagicMock()
    sys.modules['homeassistant.components.sensor'] = MagicMock()
    sys.modules['homeassistant.components.binary_sensor'] = MagicMock()

    # Add Platform enum
    from enum import Enum
    class Platform(Enum):
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"

    sys.modules['homeassistant.const'].Platform = Platform
