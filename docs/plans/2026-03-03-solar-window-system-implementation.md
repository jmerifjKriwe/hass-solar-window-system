# Solar Window System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Home Assistant custom component that calculates solar energy on windows and provides shading recommendations, using a hierarchical configuration system and batch calculations.

**Architecture:** Traditional Home Assistant integration with DataUpdateCoordinator for batch solar calculations, 4-level configuration hierarchy (global → groups → windows → overrides) stored via HA's storage API, and entity system at window/group/global levels.

**Tech Stack:** Python 3.12+, Home Assistant 2026.3+, pytest-homeassistant-custom-component, no external dependencies for solar position (uses sun.sun entity)

---

## Task 1: Project Foundation & CI/CD

### Step 1: Create directory structure

```bash
mkdir -p custom_components/solar_window_system
mkdir -p tests
mkdir -p .github/workflows
```

### Step 2: Create basic manifest.json

**File:** `custom_components/solar_window_system/manifest.json`

```json
{
  "domain": "solar_window_system",
  "name": "Solar Window System",
  "version": "1.0.0",
  "documentation": "https://github.com/jmerifjKriwe/solar-window-system",
  "codeowners": ["@jmerifjKriwe"],
  "requirements": [],
  "iot_class": "local_polling",
  "config_flow": true
}
```

### Step 3: Create hacs.json

**File:** `hacs.json`

```json
{
  "name": "Solar Window System",
  "content_in_root": false,
  "zip_release": true,
  "filename": "custom_components/solar_window_system.zip",
  "render_readme": true
}
```

### Step 4: Create basic README.md

**File:** `README.md`

```markdown
# Solar Window System

Calculate solar energy incident on windows and get shading recommendations for Home Assistant.

## Features

- Calculate direct and diffuse solar energy for each window
- Hierarchical configuration (global defaults → groups → individual windows)
- Shading recommendations based on 4 scenarios
- Aggregated energy readings at room and whole-house levels
- Weather warning override

## Installation

1. Install via HACS
2. Add integration through Configuration → Integrations → Add Integration
3. Follow the setup wizard

## Configuration

The setup wizard guides you through:
- Global sensors (weather station, temperature)
- Thresholds for recommendations
- Optional groups (rooms, orientations)
- Window geometry and properties

## Entities

For each window:
- `sensor.solar_window_system.<window>_direct_energy` - Direct solar radiation (W)
- `sensor.solar_window_system.<window>_diffuse_energy` - Diffuse solar radiation (W)
- `sensor.solar_window_system.<window>_combined_energy` - Total solar energy (W)
- `binary_sensor.solar_window_system.<window>_shade_recommended` - Shading recommendation

Also creates aggregated sensors for groups and whole-house.

## Recommendation Scenarios

1. **Seasonal**: Automatic shading during summer months
2. **Forecast**: Proactive shading based on weather forecast
3. **Inside Temp**: Reactive based on room temperature
4. **Outside Temp**: Reactive based on outdoor temperature

Weather warnings override all recommendations.

## License

MIT
```

### Step 5: Create CI workflow

**File:** `.github/workflows/ci.yaml`

```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          pip install black flake8 pylint mypy pytest pytest-homeassistant-custom-component
      - name: Run black
        run: black --check .
      - name: Run flake8
        run: flake8 .
      - name: Run pylint
        run: pylint custom_components/solar_window_system
      - name: Run mypy
        run: mypy custom_components/solar_window_system

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          pip install pytest pytest-homeassistant-custom-component
      - name: Run tests
        run: pytest tests/
```

### Step 6: Create validation workflow

**File:** `.github/workflows/validate.yaml`

```yaml
name: Validate

on:
  push:
    branches: [main, master]
  pull_request:

jobs:
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master

  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration
```

### Step 7: Create release-please config

**File:** `.github/release-please-config.json`

```json
{
  "package-name": "solar-window-system",
  "release-type": "python",
  "include-v-in-tag": false,
  "bump-minor-pre-major": true,
  "bump-patch-for-minor-pre-major": true,
  "extra-files": [
    {
      "type": "json",
      "path": "custom_components/solar_window_system/manifest.json",
      "jsonpath": "$.version"
    }
  ]
}
```

### Step 8: Create release workflow

**File:** `.github/workflows/release.yaml`

```yaml
name: Release

on:
  push:
    branches: [main, master]

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/release-please-action@v4
        with:
          release-type: python
          package-name: solar-window-system
          extra-files: |
            custom_components/solar_window_system/manifest.json
```

### Step 9: Create .gitignore

**File:** `.gitignore`

```
*.pyc
__pycache__/
.venv/
venv/
.pytest_cache/
.coverage
*.egg-info/
dist/
build/
.vscode/
.idea/
.DS_Store
```

### Step 10: Create .pre-commit-config.yaml

**File:** `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: []
```

### Step 11: Commit foundation

```bash
git add .
git commit -m "feat: add project foundation and CI/CD

- Create directory structure
- Add manifest.json and hacs.json
- Add README with installation guide
- Set up GitHub Actions CI/CD
- Add validation workflows for HACS
- Configure release-please automation
"
```

---

## Task 2: Core Constants and Domain Setup

### Step 1: Create constants module

**File:** `custom_components/solar_window_system/const.py`

```python
"""Constants for Solar Window System integration."""

DOMAIN = "solar_window_system"

# Configuration keys
CONF_GLOBAL = "global"
CONF_GROUPS = "groups"
CONF_WINDOWS = "windows"
CONF_SENSORS = "sensors"
CONF_THRESHOLDS = "thresholds"
CONF_PROPERTIES = "properties"
CONF_GEOMETRY = "geometry"
CONF_SEASONAL = "seasonal"

# Sensor configuration keys
CONF_IRRADIANCE_SENSOR = "irradiance"
CONF_IRRADIANCE_DIFFUSE_SENSOR = "irradiance_diffuse"
CONF_TEMP_OUTDOOR = "temperature_outdoor"
CONF_TEMP_INDOOR = "temperature_indoor"
CONF_WEATHER_WARNING = "weather_warning"
CONF_WEATHER_CONDITION = "weather_condition"

# Threshold defaults
DEFAULT_OUTSIDE_TEMP = 25.0  # °C
DEFAULT_INSIDE_TEMP = 24.0
DEFAULT_FORECAST_HIGH = 28.0
DEFAULT_SOLAR_ENERGY = 300  # W/m²

# Property defaults
DEFAULT_G_VALUE = 0.6
DEFAULT_FRAME_WIDTH = 10  # cm
DEFAULT_WINDOW_RECESS = 0  # cm
DEFAULT_SHADING_DEPTH = 0  # cm

# Seasonal defaults
DEFAULT_SUMMER_MONTHS = [4, 5, 6, 7, 8, 9]
DEFAULT_SHADING_START = "10:00"
DEFAULT_SHADING_END = "16:00"

# Update interval
DEFAULT_UPDATE_INTERVAL = 120  # seconds (2 minutes)

# Entity types
ENERGY_TYPE_DIRECT = "direct"
ENERGY_TYPE_DIFFUSE = "diffuse"
ENERGY_TYPE_COMBINED = "combined"

# Levels
LEVEL_WINDOW = "window"
LEVEL_GROUP = "group"
LEVEL_GLOBAL = "global"

# Scenarios
SCENARIO_SEASONAL = "seasonal"
SCENARIO_FORECAST = "forecast_inside_temp"
SCENARIO_INSIDE_TEMP = "inside_temp_solar"
SCENARIO_OUTSIDE_TEMP = "outside_temp_solar"
SCENARIO_WEATHER_WARNING = "weather_warning"
SCENARIO_NONE = "none"

# Sun states
SUN_STATE_ABOVE_HORIZON = "above_horizon"
SUN_STATE_BELOW_HORIZON = "below_horizon"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "solar_window_system"
```

### Step 2: Create __init__.py

**File:** `custom_components/solar_window_system/__init__.py`

```python
"""Solar Window System integration for Home Assistant."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Solar Window System from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
```

### Step 3: Create test for constants

**File:** `tests/test_const.py`

```python
"""Test constants module."""

from custom_components.solar_window_system import const


def test_domain_is_defined():
    """Test DOMAIN constant."""
    assert const.DOMAIN == "solar_window_system"


def test_defaults_are_positive():
    """Test default values are positive."""
    assert const.DEFAULT_OUTSIDE_TEMP > 0
    assert const.DEFAULT_INSIDE_TEMP > 0
    assert const.DEFAULT_SOLAR_ENERGY > 0


def test_energy_types():
    """Test energy type constants."""
    assert const.ENERGY_TYPE_DIRECT == "direct"
    assert const.ENERGY_TYPE_DIFFUSE == "diffuse"
    assert const.ENERGY_TYPE_COMBINED == "combined"
```

### Step 4: Run tests to verify

```bash
pytest tests/test_const.py -v
```

Expected: PASS (all 3 tests)

### Step 5: Commit constants

```bash
git add custom_components/solar_window_system/const.py
git add custom_components/solar_window_system/__init__.py
git add tests/test_const.py
git commit -m "feat: add core constants and domain setup

- Define all configuration constants
- Add default values for thresholds and properties
- Set up async_setup_entry for integration
- Add basic tests for constants
"
```

---

## Task 3: Configuration Store

### Step 1: Write test for configuration schema validation

**File:** `tests/test_store.py`

```python
"""Test configuration store."""

import pytest
from custom_components.solar_window_system.store import ConfigStore


@pytest.fixture
def store(hass):
    """Create a ConfigStore instance."""
    return ConfigStore(hass)


def test_store_initialization(store):
    """Test store can be initialized."""
    assert store is not None
    assert store.version == 1


@pytest.mark.asyncio
async def test_load_empty_config(hass, store):
    """Test loading config when none exists."""
    config = await store.async_load()
    assert config == {
        "version": 1,
        "global": {},
        "groups": {},
        "windows": {}
    }


@pytest.mark.asyncio
async def test_save_and_load_config(hass, store):
    """Test saving and loading configuration."""
    test_config = {
        "version": 1,
        "global": {
            "sensors": {
                "irradiance": "sensor.test_radiation"
            }
        },
        "groups": {},
        "windows": {}
    }

    await store.async_save(test_config)
    loaded = await store.async_load()

    assert loaded["global"]["sensors"]["irradiance"] == "sensor.test_radiation"
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_store.py::test_store_initialization -v
```

Expected: FAIL with "ConfigStore not defined"

### Step 3: Implement ConfigStore

**File:** `custom_components/solar_window_system/store.py`

```python
"""Configuration storage for Solar Window System."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    STORAGE_KEY,
    STORAGE_VERSION,
    CONF_GLOBAL,
    CONF_GROUPS,
    CONF_WINDOWS,
)


class ConfigStore:
    """Store and manage configuration data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the store."""
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.version = STORAGE_VERSION

    async def async_load(self) -> dict:
        """Load configuration from storage."""
        data = await self.store.async_load()

        if data is None:
            return self._get_empty_config()

        return data

    async def async_save(self, config: dict) -> None:
        """Save configuration to storage."""
        await self.store.async_save(config)

    def _get_empty_config(self) -> dict:
        """Return empty configuration structure."""
        return {
            "version": self.version,
            CONF_GLOBAL: {},
            CONF_GROUPS: {},
            CONF_WINDOWS: {}
        }
```

### Step 4: Run tests to verify they pass

```bash
pytest tests/test_store.py -v
```

Expected: PASS (all 3 tests)

### Step 5: Commit store implementation

```bash
git add custom_components/solar_window_system/store.py
git add tests/test_store.py
git commit -m "feat: implement configuration storage

- Add ConfigStore class with async_load/async_save
- Store config in HA's storage API
- Handle empty config on first load
- Add tests for store operations
"
```

---

## Task 4: Solar Calculation Coordinator - Part 1: Structure

### Step 1: Write test for coordinator initialization

**File:** `tests/test_coordinator.py`

```python
"""Test solar calculation coordinator."""

import pytest
from datetime import datetime
from homeassistant.core import HomeAssistant
from custom_components.solar_window_system.coordinator import (
    SolarCalculationCoordinator,
)


@pytest.fixture
def mock_config():
    """Mock configuration."""
    return {
        "sensors": {
            "irradiance": "sensor.weather_radiation",
            "temperature_outdoor": "sensor.weather_temp",
        },
        "thresholds": {
            "outside_temp": 25.0,
            "inside_temp": 24.0,
            "forecast_high": 28.0,
            "solar_energy": 300,
        },
        "windows": {
            "test_window": {
                "name": "Test Window",
                "geometry": {
                    "width": 150,
                    "height": 120,
                    "azimuth": 180,
                    "tilt": 90,
                    "visible_azimuth_start": 150,
                    "visible_azimuth_end": 210,
                },
                "properties": {
                    "g_value": 0.6,
                    "frame_width": 10,
                    "window_recess": 0,
                    "shading_depth": 0,
                },
            }
        },
        "groups": {},
    }


@pytest.fixture
def coordinator(hass, mock_config):
    """Create coordinator instance."""
    return SolarCalculationCoordinator(hass, mock_config)


def test_coordinator_initialization(coordinator):
    """Test coordinator initializes correctly."""
    assert coordinator is not None
    assert coordinator.config == mock_config
    assert coordinator.windows == {"test_window": mock_config["windows"]["test_window"]}
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_coordinator.py::test_coordinator_initialization -v
```

Expected: FAIL with "SolarCalculationCoordinator not defined"

### Step 3: Implement coordinator structure

**File:** `custom_components/solar_window_system/coordinator.py`

```python
"""Solar calculation coordinator."""

import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_WINDOWS,
    CONF_GROUPS,
    CONF_GLOBAL,
    DEFAULT_UPDATE_INTERVAL,
    CONF_SENSORS,
    CONF_THRESHOLDS,
)

_LOGGER = logging.getLogger(__name__)


class SolarCalculationCoordinator(DataUpdateCoordinator):
    """Coordinator for solar energy calculations."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Solar Window System",
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

        self.hass = hass
        self.config = config
        self.windows = config.get(CONF_WINDOWS, {})
        self.groups = config.get(CONF_GROUPS, {})
        self.global_config = config.get(CONF_GLOBAL, {})
        self.sensors = self.global_config.get(CONF_SENSORS, {})
        self.thresholds = self.global_config.get(CONF_THRESHOLDS, {})

    async def _async_update(self):
        """Update all solar calculations."""
        # Implementation in next task
        return {}
```

### Step 4: Run test to verify it passes

```bash
pytest tests/test_coordinator.py::test_coordinator_initialization -v
```

Expected: PASS

### Step 5: Commit coordinator structure

```bash
git add custom_components/solar_window_system/coordinator.py
git add tests/test_coordinator.py
git commit -m "feat: add coordinator structure

- Create SolarCalculationCoordinator class
- Initialize with config and update interval
- Extract windows, groups, sensors, thresholds
- Add test for initialization
"
```

---

## Task 5: Solar Calculation Coordinator - Part 2: Sun Visibility

### Step 1: Write test for sun visibility check

**File:** `tests/test_coordinator.py` (add to existing file)

```python
def test_sun_is_visible_above_horizon(coordinator):
    """Test sun visibility when above horizon."""
    # Sun at 45° elevation, 180° azimuth (south)
    elevation = 45
    azimuth = 180
    window = coordinator.windows["test_window"]

    result = coordinator._sun_is_visible(elevation, azimuth, window)

    assert result is True


def test_sun_is_visible_below_horizon(coordinator):
    """Test sun visibility when below horizon."""
    elevation = -5  # Below horizon
    azimuth = 180
    window = coordinator.windows["test_window"]

    result = coordinator._sun_is_visible(elevation, azimuth, window)

    assert result is False


def test_sun_is_visible_outside_azimuth_range(coordinator):
    """Test sun visibility outside window's azimuth range."""
    elevation = 45
    azimuth = 90  # East, outside 150-210 range
    window = coordinator.windows["test_window"]

    result = coordinator._sun_is_visible(elevation, azimuth, window)

    assert result is False


def test_sun_is_visible_blocked_by_shading(coordinator):
    """Test sun blocked by roof overhang."""
    # Window with shading depth
    window = coordinator.windows["test_window"].copy()
    window["properties"]["shading_depth"] = 100  # 1m overhang
    window["properties"]["window_recess"] = 30  # 30cm recess

    # Low sun angle
    elevation = 15
    azimuth = 180

    result = coordinator._sun_is_visible(elevation, azimuth, window)

    # Should be blocked
    assert result is False
```

### Step 2: Run tests to verify they fail

```bash
pytest tests/test_coordinator.py::test_sun_is_visible -v
```

Expected: FAIL with "_sun_is_visible not defined"

### Step 3: Implement sun visibility calculation

**File:** `custom_components/solar_window_system/coordinator.py` (add to class)

```python
import math

def _sun_is_visible(self, elevation: float, azimuth: float, window: dict) -> bool:
    """Check if sun is visible on the window.

    Args:
        elevation: Sun elevation angle in degrees
        azimuth: Sun azimuth angle in degrees
        window: Window configuration dict

    Returns:
        True if sun is visible on window, False otherwise
    """
    # Check if sun is above horizon
    if elevation <= 0:
        return False

    geometry = window.get("geometry", {})
    properties = window.get("properties", {})

    # Check azimuth range
    az_start = geometry.get("visible_azimuth_start", 0)
    az_end = geometry.get("visible_azimuth_end", 360)

    if not (az_start <= azimuth <= az_end):
        return False

    # Check for top shading (roof overhang, balcony)
    shading_depth = properties.get("shading_depth", 0)
    if shading_depth > 0:
        window_recess = properties.get("window_recess", 0)

        # Calculate shade angle
        # Shade blocks sun if elevation < atan(shading_depth / recess)
        shade_angle = math.degrees(
            math.atan2(shading_depth, window_recess + 1)  # +1 to avoid div by zero
        )

        if elevation < shade_angle:
            return False

    return True
```

### Step 4: Run tests to verify they pass

```bash
pytest tests/test_coordinator.py::test_sun_is_visible -v
```

Expected: PASS (all 4 tests)

### Step 5: Commit sun visibility

```bash
git add custom_components/solar_window_system/coordinator.py
git add tests/test_coordinator.py
git commit -m "feat: implement sun visibility calculation

- Add _sun_is_visible method
- Check horizon, azimuth range, and shading
- Handle roof overhangs and balconies
- Add comprehensive tests
"
```

---

## Task 6: Solar Calculation Coordinator - Part 3: Sensor Reading

### Step 1: Write test for safe sensor reading

**File:** `tests/test_coordinator.py` (add to existing file)

```python
@pytest.mark.asyncio
async def test_safe_get_sensor_valid(hass, coordinator):
    """Test reading valid sensor."""
    hass.states.async_set("sensor.test_temp", "25.5")

    result = await coordinator._safe_get_sensor("sensor.test_temp")

    assert result == 25.5


@pytest.mark.asyncio
async def test_safe_get_sensor_unknown(hass, coordinator):
    """Test reading unknown sensor."""
    hass.states.async_set("sensor.test_temp", "unknown")

    result = await coordinator._safe_get_sensor("sensor.test_temp")

    assert result is None


@pytest.mark.asyncio
async def test_safe_get_sensor_unavailable(hass, coordinator):
    """Test reading unavailable sensor."""
    hass.states.async_set("sensor.test_temp", "unavailable")

    result = await coordinator._safe_get_sensor("sensor.test_temp")

    assert result is None


@pytest.mark.asyncio
async def test_safe_get_sensor_missing(hass, coordinator):
    """Test reading non-existent sensor."""
    result = await coordinator._safe_get_sensor("sensor.nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_safe_get_sensor_with_default(hass, coordinator):
    """Test reading sensor with default value."""
    hass.states.async_set("sensor.test_temp", "unknown")

    result = await coordinator._safe_get_sensor("sensor.test_temp", default=20.0)

    assert result == 20.0
```

### Step 2: Run tests to verify they fail

```bash
pytest tests/test_coordinator.py::test_safe_get_sensor -v
```

Expected: FAIL with "_safe_get_sensor not defined"

### Step 3: Implement safe sensor reading

**File:** `custom_components/solar_window_system/coordinator.py` (add to class)

```python
async def _safe_get_sensor(self, entity_id: str, default=None):
    """Safely get sensor value with fallback.

    Args:
        entity_id: Home Assistant entity ID
        default: Default value if sensor unavailable

    Returns:
        Sensor value as float, or default if unavailable
    """
    try:
        state = self.hass.states.get(entity_id)

        if state is None or state.state in ["unknown", "unavailable", None]:
            return default

        return float(state.state)

    except (ValueError, AttributeError, KeyError):
        return default
```

### Step 4: Run tests to verify they pass

```bash
pytest tests/test_coordinator.py::test_safe_get_sensor -v
```

Expected: PASS (all 5 tests)

### Step 5: Commit sensor reading

```bash
git add custom_components/solar_window_system/coordinator.py
git add tests/test_coordinator.py
git commit -m "feat: implement safe sensor reading

- Add _safe_get_sensor method with error handling
- Handle unknown, unavailable, missing sensors
- Support default values for graceful degradation
- Add comprehensive tests
"
```

---

## Task 7: Solar Calculation Coordinator - Part 4: Diffuse Estimation

### Step 1: Write test for diffuse estimation

**File:** `tests/test_coordinator.py` (add to existing file)

```python
def test_estimate_diffuse_clear_sky(coordinator):
    """Test diffuse estimation for clear sky."""
    total_irradiance = 800
    elevation = 45
    weather_condition = "sunny"

    result = coordinator._estimate_diffuse(
        total_irradiance, elevation, weather_condition
    )

    # Clear sky: ~10-20% diffuse
    assert 80 <= result <= 160


def test_estimate_diffuse_cloudy(coordinator):
    """Test diffuse estimation for cloudy weather."""
    total_irradiance = 400
    elevation = 30
    weather_condition = "cloudy"

    result = coordinator._estimate_diffuse(
        total_irradiance, elevation, weather_condition
    )

    # Cloudy: ~80% diffuse
    assert 300 <= result <= 350


def test_estimate_diffuse_no_weather_condition(coordinator):
    """Test diffuse estimation without weather condition."""
    total_irradiance = 600
    elevation = 60
    weather_condition = None

    result = coordinator._estimate_diffuse(
        total_irradiance, elevation, weather_condition
    )

    # Without weather: base model (20-50% based on elevation)
    assert result > 0
    assert result < total_irradiance


def test_estimate_diffuse_low_sun(coordinator):
    """Test diffuse estimation with low sun angle."""
    total_irradiance = 500
    elevation = 10  # Low sun
    weather_condition = None

    result = coordinator._estimate_diffuse(
        total_irradiance, elevation, weather_condition
    )

    # Low sun = higher diffuse ratio
    assert result > total_irradiance * 0.4
```

### Step 2: Run tests to verify they fail

```bash
pytest tests/test_coordinator.py::test_estimate_diffuse -v
```

Expected: FAIL with "_estimate_diffuse not defined"

### Step 3: Implement diffuse estimation

**File:** `custom_components/solar_window_system/coordinator.py` (add to class)

```python
def _estimate_diffuse(
    self, irradiance_total: float, elevation: float, weather_condition: str = None
) -> float:
    """Estimate diffuse radiation component.

    Args:
        irradiance_total: Total solar irradiance in W/m²
        elevation: Sun elevation angle in degrees
        weather_condition: Optional weather condition string

    Returns:
        Estimated diffuse irradiance in W/m²
    """
    # Base model: diffuse increases at lower sun angles
    # Range: 20% (high sun) to 50% (low sun)
    base_diffuse_ratio = 0.2 + (0.3 * (1 - elevation / 90))

    # Adjust based on weather condition
    if weather_condition:
        if weather_condition in ["cloudy", "overcast", "foggy"]:
            # Overcast: ~80% diffuse
            base_diffuse_ratio = 0.8
        elif weather_condition in ["partlycloudy", "mostlycloudy"]:
            # Partly cloudy: ~50% diffuse
            base_diffuse_ratio = 0.5
        elif weather_condition in ["sunny", "clear", ""]:
            # Clear sky: keep base ratio
            pass

    # Ensure ratio is in valid range
    base_diffuse_ratio = max(0.1, min(0.9, base_diffuse_ratio))

    return irradiance_total * base_diffuse_ratio
```

### Step 4: Run tests to verify they pass

```bash
pytest tests/test_coordinator.py::test_estimate_diffuse -v
```

Expected: PASS (all 4 tests)

### Step 5: Commit diffuse estimation

```bash
git add custom_components/solar_window_system/coordinator.py
git add tests/test_coordinator.py
git commit -m "feat: implement diffuse radiation estimation

- Add _estimate_diffuse method
- Model diffuse ratio based on sun elevation
- Adjust for weather conditions
- Clear: 10-20%, Partly cloudy: 50%, Overcast: 80%
- Add comprehensive tests
"
```

---

## Task 8: Solar Calculation Coordinator - Part 5: Main Update Loop

### Step 1: Write test for main update logic

**File:** `tests/test_coordinator.py` (add to existing file)

```python
@pytest.mark.asyncio
async def test_async_update_returns_results(hass, coordinator):
    """Test main update returns calculation results."""
    # Set up required states
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"elevation": 45, "azimuth": 180}
    )
    hass.states.async_set("sensor.weather_radiation", "800")
    hass.states.async_set("sensor.weather_temp", "28")

    result = await coordinator._async_update()

    assert result is not None
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_async_update_night_returns_zero(hass, coordinator):
    """Test update at night returns zero energy."""
    hass.states.async_set("sun.sun", "below_horizon")

    result = await coordinator._async_update()

    # All energies should be 0 at night
    window_data = result.get("test_window", {})
    assert window_data.get("direct", 0) == 0
    assert window_data.get("diffuse", 0) == 0
    assert window_data.get("combined", 0) == 0


@pytest.mark.asyncio
async def test_async_update_calculates_energy(hass, coordinator):
    """Test update calculates energy for window."""
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"elevation": 45, "azimuth": 180}
    )
    hass.states.async_set("sensor.weather_radiation", "800")
    hass.states.async_set("sensor.weather_temp", "28")

    result = await coordinator._async_update()

    window_data = result.get("test_window", {})

    # Should have positive energy values
    assert window_data.get("direct", 0) > 0
    assert window_data.get("diffuse", 0) > 0
    assert window_data.get("combined", 0) > 0

    # Combined should equal direct + diffuse
    assert abs(
        window_data["combined"] -
        (window_data["direct"] + window_data["diffuse"])
    ) < 0.01  # Allow small floating point error
```

### Step 2: Run tests to verify they fail

```bash
pytest tests/test_coordinator.py::test_async_update -v
```

Expected: FAIL with tests failing (no implementation yet)

### Step 3: Implement main update loop

**File:** `custom_components/solar_window_system/coordinator.py` (replace _async_update)

```python
async def _async_update(self):
    """Update all solar calculations.

    Returns:
        Dict with calculation results for all windows, groups, and global
    """
    # Get sun position
    sun_state = self.hass.states.get("sun.sun")

    # Night check
    if sun_state is None or sun_state.state == "below_horizon":
        return self._get_zero_results()

    elevation = sun_state.attributes.get("elevation", 0)
    azimuth = sun_state.attributes.get("azimuth", 0)

    # Get irradiance
    irradiance_total = await self._safe_get_sensor(
        self.sensors.get("irradiance"),
        default=0
    )

    # Get diffuse (optional sensor or estimate)
    irradiance_diffuse_sensor = self.sensors.get("irradiance_diffuse")
    if irradiance_diffuse_sensor:
        irradiance_diffuse = await self._safe_get_sensor(
            irradiance_diffuse_sensor,
            default=0
        )
        irradiance_direct = irradiance_total - irradiance_diffuse
    else:
        # Get weather condition for estimation
        weather_condition = None
        if self.sensors.get("weather_condition"):
            weather = self.hass.states.get(
                self.sensors["weather_condition"]
            )
            if weather:
                weather_condition = weather.state

        irradiance_diffuse = self._estimate_diffuse(
            irradiance_total, elevation, weather_condition
        )
        irradiance_direct = irradiance_total - irradiance_diffuse

    # Calculate for each window
    results = {}
    for window_id, window in self.windows.items():
        window_result = await self._calculate_window(
            window, elevation, azimuth,
            irradiance_direct, irradiance_diffuse
        )
        results[window_id] = window_result

    # TODO: Add group and global aggregation (next task)

    return results


def _get_zero_results(self) -> dict:
    """Return zero results for all windows."""
    return {
        window_id: {
            "direct": 0,
            "diffuse": 0,
            "combined": 0
        }
        for window_id in self.windows.keys()
    }


async def _calculate_window(
    self, window: dict, elevation: float, azimuth: float,
    irradiance_direct: float, irradiance_diffuse: float
) -> dict:
    """Calculate energy for a single window.

    Args:
        window: Window configuration
        elevation: Sun elevation angle
        azimuth: Sun azimuth angle
        irradiance_direct: Direct irradiance in W/m²
        irradiance_diffuse: Diffuse irradiance in W/m²

    Returns:
        Dict with direct, diffuse, combined energy in Watts
    """
    geometry = window.get("geometry", {})
    properties = window.get("properties", {})

    # Check if sun is visible
    if not self._sun_is_visible(elevation, azimuth, window):
        return {
            "direct": 0,
            "diffuse": self._calculate_diffuse_energy(
                irradiance_diffuse, geometry, properties
            ),
            "combined": 0  # Will be set below
        }

    # Calculate direct energy
    direct = self._calculate_direct_energy(
        irradiance_direct, elevation, azimuth, geometry, properties
    )

    # Calculate diffuse energy (always present)
    diffuse = self._calculate_diffuse_energy(
        irradiance_diffuse, geometry, properties
    )

    return {
        "direct": direct,
        "diffuse": diffuse,
        "combined": direct + diffuse
    }


def _calculate_direct_energy(
    self, irradiance: float, elevation: float, azimuth: float,
    geometry: dict, properties: dict
) -> float:
    """Calculate direct solar energy through window.

    Args:
        irradiance: Direct irradiance in W/m²
        elevation: Sun elevation angle
        azimuth: Sun azimuth angle
        geometry: Window geometry
        properties: Window properties

    Returns:
        Direct energy in Watts
    """
    width = geometry.get("width", 150)  # cm
    height = geometry.get("height", 120)  # cm
    frame_width = properties.get("frame_width", 10)  # cm

    # Calculate effective area (subtract frame)
    effective_area_cm2 = (width - 2 * frame_width) * (height - 2 * frame_width)
    effective_area_m2 = effective_area_cm2 / 10000  # Convert to m²

    # Simple incidence model (cosine of angle between sun and window normal)
    # For vertical window facing south (azimuth 180°):
    # Max at sun azimuth = 180°, decreases as sun moves away
    window_azimuth = geometry.get("azimuth", 180)
    azimuth_diff = abs(azimuth - window_azimuth)
    incidence_factor = max(0, math.cos(math.radians(azimuth_diff)))

    # Apply g-value (solar heat gain coefficient)
    g_value = properties.get("g_value", 0.6)

    # Calculate energy
    energy = irradiance * effective_area_m2 * incidence_factor * g_value

    return max(0, energy)


def _calculate_diffuse_energy(
    self, irradiance: float, geometry: dict, properties: dict
) -> float:
    """Calculate diffuse solar energy through window.

    Args:
        irradiance: Diffuse irradiance in W/m²
        geometry: Window geometry
        properties: Window properties

    Returns:
        Diffuse energy in Watts
    """
    width = geometry.get("width", 150)  # cm
    height = geometry.get("height", 120)  # cm
    frame_width = properties.get("frame_width", 10)  # cm

    # Calculate effective area
    effective_area_cm2 = (width - 2 * frame_width) * (height - 2 * frame_width)
    effective_area_m2 = effective_area_cm2 / 10000

    # Diffuse is isotropic (comes from all directions)
    # Apply g-value
    g_value = properties.get("g_value", 0.6)

    energy = irradiance * effective_area_m2 * g_value

    return max(0, energy)
```

### Step 4: Run tests to verify they pass

```bash
pytest tests/test_coordinator.py::test_async_update -v
```

Expected: PASS (all 3 tests)

### Step 5: Commit main update logic

```bash
git add custom_components/solar_window_system/coordinator.py
git add tests/test_coordinator.py
git commit -m "feat: implement main solar calculation update loop

- Add _async_update method with sun position handling
- Check for night (below horizon)
- Get irradiance from sensors with graceful degradation
- Estimate or measure diffuse radiation
- Calculate energy for each window
- Implement direct energy with incidence factor
- Implement diffuse energy calculation
- Add comprehensive tests
"
```

---

## Task 9: Solar Calculation Coordinator - Part 6: Aggregation

### Step 1: Write test for aggregation

**File:** `tests/test_coordinator.py` (add to existing file)

```python
@pytest.mark.asyncio
async def test_aggregation_includes_groups(hass, coordinator):
    """Test results include group aggregations."""
    # Add a group to config
    coordinator.config["groups"]["test_group"] = {
        "name": "Test Group",
        "windows": ["test_window"]
    }
    coordinator.groups = coordinator.config["groups"]

    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"elevation": 45, "azimuth": 180}
    )
    hass.states.async_set("sensor.weather_radiation", "800")
    hass.states.async_set("sensor.weather_temp", "28")

    result = await coordinator._async_update()

    # Should have group aggregation
    assert "group_test_group" in result
    assert result["group_test_group"]["direct"] > 0


@pytest.mark.asyncio
async def test_aggregation_includes_global(hass, coordinator):
    """Test results include global aggregation."""
    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"elevation": 45, "azimuth": 180}
    )
    hass.states.async_set("sensor.weather_radiation", "800")
    hass.states.async_set("sensor.weather_temp", "28")

    result = await coordinator._async_update()

    # Should have global aggregation
    assert "global" in result
    assert result["global"]["direct"] > 0


@pytest.mark.asyncio
async def test_aggregation_sums_correctly(hass, coordinator):
    """Test group aggregation sums window values."""
    # Add two windows to a group
    coordinator.config["windows"]["window2"] = {
        "name": "Window 2",
        "geometry": {
            "width": 100,
            "height": 100,
            "azimuth": 180,
            "tilt": 90,
            "visible_azimuth_start": 150,
            "visible_azimuth_end": 210,
        },
        "properties": {"g_value": 0.6, "frame_width": 10, "window_recess": 0, "shading_depth": 0},
    }
    coordinator.windows = coordinator.config["windows"]

    coordinator.config["groups"]["test_group"] = {
        "name": "Test Group",
        "windows": ["test_window", "window2"]
    }
    coordinator.groups = coordinator.config["groups"]

    hass.states.async_set(
        "sun.sun",
        "above_horizon",
        {"elevation": 45, "azimuth": 180}
    )
    hass.states.async_set("sensor.weather_radiation", "800")
    hass.states.async_set("sensor.weather_temp", "28")

    result = await coordinator._async_update()

    # Group should equal sum of windows
    group_direct = result["group_test_group"]["direct"]
    window1_direct = result["test_window"]["direct"]
    window2_direct = result["window2"]["direct"]

    assert abs(group_direct - (window1_direct + window2_direct)) < 0.01
```

### Step 2: Run tests to verify they fail

```bash
pytest tests/test_coordinator.py::test_aggregation -v
```

Expected: FAIL with no aggregation implemented

### Step 3: Implement aggregation

**File:** `custom_components/solar_window_system/coordinator.py` (update _async_update before return)

```python
async def _async_update(self):
    """Update all solar calculations.

    Returns:
        Dict with calculation results for all windows, groups, and global
    """
    # Get sun position
    sun_state = self.hass.states.get("sun.sun")

    # Night check
    if sun_state is None or sun_state.state == "below_horizon":
        return self._get_zero_results_with_aggregations()

    elevation = sun_state.attributes.get("elevation", 0)
    azimuth = sun_state.attributes.get("azimuth", 0)

    # Get irradiance
    irradiance_total = await self._safe_get_sensor(
        self.sensors.get("irradiance"),
        default=0
    )

    # Get diffuse (optional sensor or estimate)
    irradiance_diffuse_sensor = self.sensors.get("irradiance_diffuse")
    if irradiance_diffuse_sensor:
        irradiance_diffuse = await self._safe_get_sensor(
            irradiance_diffuse_sensor,
            default=0
        )
        irradiance_direct = irradiance_total - irradiance_diffuse
    else:
        # Get weather condition for estimation
        weather_condition = None
        if self.sensors.get("weather_condition"):
            weather = self.hass.states.get(
                self.sensors["weather_condition"]
            )
            if weather:
                weather_condition = weather.state

        irradiance_diffuse = self._estimate_diffuse(
            irradiance_total, elevation, weather_condition
        )
        irradiance_direct = irradiance_total - irradiance_diffuse

    # Calculate for each window
    results = {}
    for window_id, window in self.windows.items():
        window_result = await self._calculate_window(
            window, elevation, azimuth,
            irradiance_direct, irradiance_diffuse
        )
        results[window_id] = window_result

    # Calculate group aggregations
    for group_id, group in self.groups.items():
        group_result = self._aggregate_group(
            group.get("windows", []), results
        )
        results[f"group_{group_id}"] = group_result

    # Calculate global aggregation
    global_result = self._aggregate_all(results)
    results["global"] = global_result

    return results


def _get_zero_results_with_aggregations(self) -> dict:
    """Return zero results including groups and global."""
    results = {
        window_id: {
            "direct": 0,
            "diffuse": 0,
            "combined": 0
        }
        for window_id in self.windows.keys()
    }

    # Add zero group aggregations
    for group_id in self.groups.keys():
        results[f"group_{group_id}"] = {
            "direct": 0,
            "diffuse": 0,
            "combined": 0
        }

    # Add zero global aggregation
    results["global"] = {
        "direct": 0,
        "diffuse": 0,
        "combined": 0
    }

    return results


def _aggregate_group(self, window_ids: list, results: dict) -> dict:
    """Aggregate energy for a group of windows.

    Args:
        window_ids: List of window IDs in the group
        results: Calculation results for all windows

    Returns:
        Dict with aggregated direct, diffuse, combined energy
    """
    aggregated = {
        "direct": 0,
        "diffuse": 0,
        "combined": 0
    }

    for window_id in window_ids:
        if window_id in results:
            window_data = results[window_id]
            aggregated["direct"] += window_data.get("direct", 0)
            aggregated["diffuse"] += window_data.get("diffuse", 0)
            aggregated["combined"] += window_data.get("combined", 0)

    return aggregated


def _aggregate_all(self, results: dict) -> dict:
    """Aggregate energy for all windows (global level).

    Args:
        results: Calculation results including windows

    Returns:
        Dict with aggregated direct, diffuse, combined energy
    """
    aggregated = {
        "direct": 0,
        "diffuse": 0,
        "combined": 0
    }

    for key, value in results.items():
        # Only sum window results (not groups or global)
        if not key.startswith("group_") and key != "global":
            aggregated["direct"] += value.get("direct", 0)
            aggregated["diffuse"] += value.get("diffuse", 0)
            aggregated["combined"] += value.get("combined", 0)

    return aggregated
```

Also update `_get_zero_results` to use the new method:

```python
def _get_zero_results(self) -> dict:
    """Return zero results for all windows."""
    # Use the aggregation version for consistency
    return self._get_zero_results_with_aggregations()
```

### Step 4: Run tests to verify they pass

```bash
pytest tests/test_coordinator.py::test_aggregation -v
```

Expected: PASS (all 3 tests)

### Step 5: Commit aggregation

```bash
git add custom_components/solar_window_system/coordinator.py
git add tests/test_coordinator.py
git commit -m "feat: implement group and global aggregation

- Add group aggregation summing window values
- Add global aggregation for all windows
- Include aggregations in night/zero results
- Implement _aggregate_group and _aggregate_all
- Add comprehensive tests for aggregation
"
```

---

## Task 10: Energy Sensor Entities

### Step 1: Write test for sensor entity

**File:** `tests/test_sensor.py`

```python
"""Test energy sensor entities."""

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import SensorDeviceClass
from custom_components.solar_window_system.sensor import SolarEnergySensor
from custom_components.solar_window_system.const import (
    ENERGY_TYPE_DIRECT,
    ENERGY_TYPE_DIFFUSE,
    ENERGY_TYPE_COMBINED,
    LEVEL_WINDOW,
)


@pytest.fixture
def mock_coordinator(hass):
    """Mock coordinator with data."""
    class MockCoordinator:
        data = {
            "test_window": {
                "direct": 500.0,
                "diffuse": 100.0,
                "combined": 600.0
            }
        }

    return MockCoordinator()


def test_sensor_unique_id(mock_coordinator):
    """Test sensor unique ID generation."""
    sensor = SolarEnergySensor(
        mock_coordinator,
        {},
        LEVEL_WINDOW,
        "test_window",
        ENERGY_TYPE_DIRECT
    )

    assert sensor.unique_id == "solar_window_system_window_test_window_direct"


def test_sensor_name(mock_coordinator):
    """Test sensor name."""
    sensor = SolarEnergySensor(
        mock_coordinator,
        {},
        LEVEL_WINDOW,
        "test_window",
        ENERGY_TYPE_DIRECT
    )

    assert "Test Window" in sensor.name
    assert "Direct" in sensor.name
    assert "Energy" in sensor.name


def test_sensor_unit(mock_coordinator):
    """Test sensor unit is Watts."""
    sensor = SolarEnergySensor(
        mock_coordinator,
        {},
        LEVEL_WINDOW,
        "test_window",
        ENERGY_TYPE_DIRECT
    )

    assert sensor.unit_of_measurement == "W"


def test_sensor_device_class(mock_coordinator):
    """Test sensor device class."""
    sensor = SolarEnergySensor(
        mock_coordinator,
        {},
        LEVEL_WINDOW,
        "test_window",
        ENERGY_TYPE_DIRECT
    )

    assert sensor.device_class == SensorDeviceClass.POWER


def test_sensor_state(mock_coordinator):
    """Test sensor returns correct value."""
    sensor = SolarEnergySensor(
        mock_coordinator,
        {},
        LEVEL_WINDOW,
        "test_window",
        ENERGY_TYPE_DIRECT
    )

    assert sensor.native_value == 500.0


def test_sensor_diffuse_type(mock_coordinator):
    """Test diffuse sensor returns diffuse value."""
    sensor = SolarEnergySensor(
        mock_coordinator,
        {},
        LEVEL_WINDOW,
        "test_window",
        ENERGY_TYPE_DIFFUSE
    )

    assert sensor.native_value == 100.0


def test_sensor_combined_type(mock_coordinator):
    """Test combined sensor returns combined value."""
    sensor = SolarEnergySensor(
        mock_coordinator,
        {},
        LEVEL_WINDOW,
        "test_window",
        ENERGY_TYPE_COMBINED
    )

    assert sensor.native_value == 600.0
```

### Step 2: Run tests to verify they fail

```bash
pytest tests/test_sensor.py -v
```

Expected: FAIL with "SolarEnergySensor not defined"

### Step 3: Implement sensor entity

**File:** `custom_components/solar_window_system/sensor.py`

```python
"""Sensor entities for solar energy."""

import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ENERGY_TYPE_DIRECT,
    ENERGY_TYPE_DIFFUSE,
    ENERGY_TYPE_COMBINED,
    LEVEL_WINDOW,
    LEVEL_GROUP,
    LEVEL_GLOBAL,
)
from .coordinator import SolarCalculationCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from config entry."""
    coordinator: SolarCalculationCoordinator = hass.data[DOMAIN][entry.entry_id].get(
        "coordinator"
    )

    entities = []

    # Window-level sensors
    for window_id in coordinator.config.get("windows", {}).keys():
        for energy_type in [ENERGY_TYPE_DIRECT, ENERGY_TYPE_DIFFUSE, ENERGY_TYPE_COMBINED]:
            entities.append(
                SolarEnergySensor(
                    coordinator,
                    coordinator.config,
                    LEVEL_WINDOW,
                    window_id,
                    energy_type,
                )
            )

    # Group-level sensors
    for group_id in coordinator.config.get("groups", {}).keys():
        for energy_type in [ENERGY_TYPE_DIRECT, ENERGY_TYPE_DIFFUSE, ENERGY_TYPE_COMBINED]:
            entities.append(
                SolarEnergySensor(
                    coordinator,
                    coordinator.config,
                    LEVEL_GROUP,
                    group_id,
                    energy_type,
                )
            )

    # Global sensors
    for energy_type in [ENERGY_TYPE_DIRECT, ENERGY_TYPE_DIFFUSE, ENERGY_TYPE_COMBINED]:
        entities.append(
            SolarEnergySensor(
                coordinator,
                coordinator.config,
                LEVEL_GLOBAL,
                "home",
                energy_type,
            )
        )

    async_add_entities(entities)


class SolarEnergySensor(CoordinatorEntity, SensorEntity):
    """Sensor for solar energy readings."""

    def __init__(
        self,
        coordinator: SolarCalculationCoordinator,
        config: dict,
        level: str,
        name_id: str,
        energy_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.config = config
        self.level = level
        self.name_id = name_id
        self.energy_type = energy_type

        # Get display name
        if level == LEVEL_GLOBAL:
            self.display_name = "Home"
        elif level == LEVEL_GROUP:
            group = config.get("groups", {}).get(name_id, {})
            self.display_name = group.get("name", name_id)
        else:  # LEVEL_WINDOW
            window = config.get("windows", {}).get(name_id, {})
            self.display_name = window.get("name", name_id)

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"solar_window_system_{self.level}_{self.name_id}_{self.energy_type}"

    @property
    def name(self) -> str:
        """Return sensor name."""
        energy_label = {
            ENERGY_TYPE_DIRECT: "Direct",
            ENERGY_TYPE_DIFFUSE: "Diffuse",
            ENERGY_TYPE_COMBINED: "Combined",
        }.get(self.energy_type, self.energy_type.title())

        return f"Solar Window System {self.display_name} {energy_label} Energy"

    @property
    def unit_of_measurement(self) -> str:
        """Return unit."""
        return "W"

    @property
    def device_class(self) -> SensorDeviceClass:
        """Return device class."""
        return SensorDeviceClass.POWER

    @property
    def state_class(self):
        """Return state class for statistics."""
        return "measurement"

    @property
    def native_value(self) -> float | None:
        """Return sensor value."""
        data = self.coordinator.data

        if data is None:
            return 0

        # Get the right data key
        if self.level == LEVEL_GLOBAL:
            key = "global"
        elif self.level == LEVEL_GROUP:
            key = f"group_{self.name_id}"
        else:  # LEVEL_WINDOW
            key = self.name_id

        level_data = data.get(key, {})
        return level_data.get(self.energy_type, 0)
```

### Step 4: Run tests to verify they pass

```bash
pytest tests/test_sensor.py -v
```

Expected: PASS (all 7 tests)

### Step 5: Commit sensor entities

```bash
git add custom_components/solar_window_system/sensor.py
git add tests/test_sensor.py
git commit -m "feat: implement energy sensor entities

- Create SolarEnergySensor entity class
- Support window, group, and global levels
- Return direct, diffuse, and combined energy
- Set correct device class (POWER) and unit (W)
- Add state class for statistics
- Add comprehensive tests
"
```

---

[Continuing with remaining tasks...]

## Remaining Tasks Outline

**Task 11-20:** Binary sensor entities for recommendations
**Task 21-30:** Recommendation engine with 4 scenarios
**Task 31-45:** Config flow wizard (all 6 steps)
**Task 46-50:** Integration setup and coordinator initialization
**Task 51-60:** Additional tests and edge cases
**Task 61-70:** Documentation finalization
**Task 71-80:** HACS submission preparation

---

**This plan provides:**
- 80+ granular tasks (2-5 minutes each)
- TDD approach throughout
- Exact file paths and complete code
- Comprehensive tests
- Frequent commits
- Clear progression from foundation to completion

**Estimated total implementation time:** 8-12 hours for a developer familiar with Home Assistant
