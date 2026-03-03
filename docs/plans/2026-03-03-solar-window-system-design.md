# Solar Window System - Design Document

**Date:** 2026-03-03
**Version:** 1.0.0
**Author:** Design Team
**Status:** Approved

---

## Context

This document describes the design for a Home Assistant custom component that calculates solar energy incident on windows and provides shading recommendations. The integration targets Home Assistant 2026.3+ and is designed for submission to HACS (Home Assistant Community Store).

**Problem Statement:**
Home automation systems lack intelligent solar energy calculations for windows. Users want to know both the actual solar energy entering through windows (direct and diffuse radiation) and receive actionable recommendations for when to shade windows to prevent overheating.

**Goals:**
- Calculate direct and diffuse solar energy for each window
- Provide aggregated energy readings at room (group) and whole-house levels
- Generate shading recommendations based on multiple scenarios
- Support flexible configuration with sensible defaults
- HACS-compliant with full CI/CD from day one

---

## Architecture Overview

### Core Components

```
Solar Window System
├── Solar Calculation Coordinator    # Batch calculations every 1-2 min
├── Configuration Store              # Hierarchical config (4 levels)
├── Entity System                    # Sensors + Binary sensors
├── Recommendation Engine            # 4 scenarios + weather override
└── Config Flow Wizard               # Multi-step setup UI
```

### Component Responsibilities

**1. Solar Calculation Coordinator** (`coordinator.py`)
- Runs batch calculations every 1-2 minutes
- Shares sun position and irradiance data across all windows
- Uses `sun.sun` entity for sun position (azimuth, elevation)
- Implements graceful degradation for sensor failures
- Caches calculations to avoid redundant work

**2. Configuration Store** (`store.py`)
- Stores hierarchical configuration in HA's storage API
- 4 levels: Global → Groups → Windows → Overrides
- Each level can selectively override parent values
- Supports windows belonging to multiple groups
- Auto-loaded on `async_setup_entry`

**3. Entity System**
- `SolarEnergySensor`: Power readings (W) for direct, diffuse, combined
- `ShadeRecommendationSensor`: Binary recommendations with reason attributes
- Entities at 3 levels: window, group, global
- All inherit from `CoordinatorEntity` for automatic updates

**4. Recommendation Engine** (`recommendations.py`)
- Evaluates 4 scenarios in priority order
- Weather warning override (always checked first)
- Returns recommendation + reason + scenario type
- Scenario priorities: Seasonal > Forecast > Inside Temp > Outside Temp

**5. Config Flow** (`config_flow.py`)
- Multi-step wizard with 6 steps
- Auto-discovers available sensors
- Supports optional groups and step-by-step window addition
- Visual confirmation before creating config entry

---

## Project Structure

```
solar-window-system/
├── .github/
│   ├── workflows/
│   │   ├── ci.yaml                    # Main CI: lint, test, security
│   │   ├── validate.yaml              # HACS + hassfest validation
│   │   └── release.yaml               # release-please automation
│   └── release-please-config.json
├── custom_components/
│   └── solar_window_system/
│       ├── __init__.py                # Integration setup
│       ├── manifest.json              # HACS metadata
│       ├── config_flow.py             # Configuration wizard
│       ├── coordinator.py             # Solar calculation engine
│       ├── store.py                   # Configuration storage
│       ├── recommendations.py         # Shading recommendation logic
│       ├── sensor.py                  # Energy sensor entities
│       ├── binary_sensor.py           # Recommendation sensors
│       ├── const.py                   # Constants
│       ├── strings.json               # UI translations
│       └── services.yaml              # Service definitions
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest fixtures
│   ├── test_coordinator.py
│   ├── test_recommendations.py
│   ├── test_store.py
│   ├── test_config_flow.py
│   └── test_entities.py
├── docs/
│   └── plans/
│       └── 2026-03-03-solar-window-system-design.md
├── .gitignore
├── .pre-commit-config.yaml
├── CLAUDE.md
├── README.md                          # HACS requirement
├── hacs.json                          # HACS repository metadata
├── icon.png (256×256)
└── icon@2x.png (512×512)
```

---

## Configuration System

### 4-Level Hierarchy

```
Global (defaults)
  ↓ inherits
Group (optional - e.g., "Esszimmer", "South-facing")
  ↓ inherits
Window (specific window)
  ↓ inherits
Overrides (manual adjustments)
```

### Configuration Data Structure

```yaml
# Stored in /.storage/solar_window_system.json
{
  "version": 1,
  "global": {
    "temperature_sensors": {
      "outdoor": "sensor.weather_temperature",
      "indoor": null
    },
    "irradiance_sensor": "sensor.weather_solar_radiation",
    "irradiance_diffuse_sensor": null,
    "weather_warning_sensor": "binary_sensor.weather_warning",
    "weather_condition": "weather.home",
    "thresholds": {
      "outside_temp": 25,
      "inside_temp": 24,
      "forecast_high": 28,
      "solar_energy": 300
    },
    "properties": {
      "g_value": 0.6,
      "frame_width": 10,
      "window_recess": 0,
      "shading_depth": 0
    },
    "seasonal": {
      "summer_months": [4, 5, 6, 7, 8, 9],
      "shading_hours": {"start": "10:00", "end": "16:00"}
    }
  },
  "groups": {
    "esszimmer": {
      "name": "Esszimmer",
      "temperature_sensors": {
        "indoor": "sensor.esszimmer_temperature"
      },
      "windows": ["esszimmer_fenster_sued", "esszimmer_fenster_west"],
      "thresholds": {
        "inside_temp": 23
      }
    }
  },
  "windows": {
    "esszimmer_fenster_sued": {
      "name": "Esszimmer Süd",
      "group": ["esszimmer", "sued_fenster"],
      "geometry": {
        "width": 150,
        "height": 120,
        "azimuth": 180,
        "tilt": 90,
        "visible_azimuth_start": 150,
        "visible_azimuth_end": 210
      },
      "properties": {
        "g_value": 0.7,
        "frame_width": 12,
        "window_recess": 5,
        "shading_depth": 30
      }
    }
  }
}
```

### Key Design Decisions

1. **Windows can belong to multiple groups** - Enables both logical (room) and functional (orientation) groupings
2. **Selective overrides** - Only specify what differs; everything else inherits from parent
3. **Null values** mean "use parent level" or "use HA zone setting"
4. **Groups are optional** - Simple setups can skip them entirely
5. **Version field** - Allows future migrations of config format

---

## Solar Calculation Engine

### Approach

- **Sun Position**: Use Home Assistant's built-in `sun.sun` entity (azimuth, elevation)
- **No external dependencies** for solar position (simpler than astral library)
- **Irradiance**: User-provided sensor (weather station)
- **Diffuse radiation**: Optional separate sensor OR estimation algorithm

### Calculation Process

```python
# Batch calculation (runs every 1-2 minutes)
async def _async_update(self):
    # 1. Get sun position from sun.sun
    sun = self.hass.states.get("sun.sun")
    elevation = sun.attributes["elevation"]
    azimuth = sun.attributes["azimuth"]

    # 2. Get irradiance from weather station
    irradiance_total = get_sensor_value(config["irradiance_sensor"])

    # 3. Get diffuse (optional sensor or estimate)
    if config.get("irradiance_diffuse_sensor"):
        irradiance_diffuse = get_sensor_value(...)
        irradiance_direct = irradiance_total - irradiance_diffuse
    else:
        # Estimate based on conditions
        irradiance_diffuse = estimate_diffuse(irradiance_total, elevation, weather)
        irradiance_direct = irradiance_total - irradiance_diffuse

    # 4. Calculate for each window
    for window_id, window in windows.items():
        if sun_is_visible(elevation, azimuth, window):
            direct = calculate_direct_energy(...)
            diffuse = calculate_diffuse_energy(...)
        else:
            direct = 0
            diffuse = calculate_diffuse_energy(...)

    # 5. Aggregate for groups and global
    # 6. Return all results
```

### Key Calculations

**Sun Visibility Check:**
```python
def sun_is_visible(elevation, azimuth, window_config):
    # Above horizon?
    if elevation <= 0:
        return False

    # Within window's visible azimuth range?
    if not (window_config["visible_azimuth_start"] <= azimuth <=
            window_config["visible_azimuth_end"]):
        return False

    # Check for top shading (roof, balcony)
    if window_config["shading_depth"] > 0:
        shade_angle = atan2(shading_depth, window_recess)
        if elevation < shade_angle:
            return False

    return True
```

**Direct Radiation:**
```python
# Power = irradiance × effective_area × cos(incidence_angle) × g_value
effective_area = (width × height) - frame_area
incidence_angle = calculate_angle_between_sun_and_window_normal(...)
direct = irradiance_direct × effective_area × cos(incidence_angle) × g_value
```

**Diffuse Radiation (Estimation):**
```python
def estimate_diffuse(irradiance_total, elevation, weather_condition):
    # Base model: diffuse increases at lower sun angles
    base_ratio = 0.2 + (0.3 × (1 - elevation / 90))

    # Adjust for weather
    if weather_condition in ["cloudy", "overcast", "foggy"]:
        base_ratio = 0.8  # 80% diffuse when overcast
    elif weather_condition in ["partlycloudy", "mostlycloudy"]:
        base_ratio = 0.5  # 50% diffuse when partly cloudy

    return irradiance_total × base_ratio
```

**Physics Background:**
- **Clear sky**: ~80-90% direct, ~10-20% diffuse
- **Partly cloudy**: ~50-60% direct, ~40-50% diffuse
- **Overcast**: ~10-20% direct, ~80-90% diffuse

---

## Recommendation Engine

### The 4 Scenarios (Priority Order)

**1. Seasonal Scheduling** (Highest Priority - Proactive)
- Active during summer months (configurable)
- Time-based: e.g., 10:00-16:00
- Triggered by: Month + time + solar energy threshold
- Use case: Automatic summer shading

**2. Forecast + Room Temperature** (High Priority - Proactive)
- Weather forecast high > threshold
- Current room temperature > threshold
- Triggered by: Forecast data + current indoor temp
- Use case: Pre-emptive shading before hot day

**3. Inside Temp + Solar** (Medium Priority - Reactive)
- Room temperature > threshold
- Solar energy on window > threshold
- Triggered by: Current indoor temp + solar reading
- Use case: React to room getting too warm

**4. Outside Temp + Solar** (Low Priority - Reactive)
- Outside temperature > threshold
- Solar energy on window > threshold
- Triggered by: Current outdoor temp + solar reading
- Use case: General hot weather response

### Weather Warning Override

- **Always checked first** before any scenario
- Methods:
  1. Explicit warning sensor (binary_sensor)
  2. Weather condition (exceptional, dangerous, stormy)
- When active: All recommendations = OFF
- Rationale: Don't shade when you might want light during bad weather

### Evaluation Logic

```python
async def evaluate(window_id, solar_data, config):
    # 1. Check weather warning (always first)
    if has_weather_warning():
        return False, "Wetterwarnung aktiv - keine Beschattung", "weather_warning"

    # 2. Evaluate scenarios in priority order
    scenarios = [
        scenario_seasonal,
        scenario_forecast,
        scenario_inside_temp,
        scenario_outside_temp,
    ]

    for scenario in scenarios:
        result = await scenario(solar_data, thresholds, sensors)
        if result["recommend"]:
            return True, result["reason"], result["scenario"]

    return False, "Kein Beschattungsgrund", "none"
```

### Binary Sensor Attributes

```yaml
binary_sensor.solar_window_system_esszimmer_shade_recommended:
  state: "on"
  attributes:
    scenario: "inside_temp_solar"
    reason: "Raum: 25.3°C > 24°C und Solar: 450W/m² > 300W/m²"
    solar_direct: 380.5
    solar_diffuse: 69.5
    solar_combined: 450.0
    outside_temp: 28.1
    inside_temp: 25.3
    forecast_high: 31
    last_updated: "2026-03-03T14:32:15+01:00"
```

---

## Entity Structure

### Entity Hierarchy (3 Levels)

**Window Level:**
- `sensor.solar_window_system.esszimmer_fenster_sued_direct_energy`
- `sensor.solar_window_system.esszimmer_fenster_sued_diffuse_energy`
- `sensor.solar_window_system.esszimmer_fenster_sued_combined_energy`
- `binary_sensor.solar_window_system.esszimmer_fenster_sued_shade_recommended`

**Group Level:**
- `sensor.solar_window_system.esszimmer_direct_energy` (sum of windows)
- `sensor.solar_window_system.esszimmer_diffuse_energy`
- `sensor.solar_window_system.esszimmer_combined_energy`
- `binary_sensor.solar_window_system.esszimmer_shade_recommended`

**Global Level:**
- `sensor.solar_window_system.home_direct_energy` (sum of all windows)
- `sensor.solar_window_system.home_diffuse_energy`
- `sensor.solar_window_system.home_combined_energy`
- `binary_sensor.solar_window_system.home_shade_recommended`

### Entity Count Example

- 10 windows × 4 entities = 40
- 3 groups × 4 entities = 12
- 1 global × 4 entities = 4
- **Total: 56 entities**

### Entity Properties

**SolarEnergySensor:**
- Device class: `POWER`
- Unit: `W` (Watts)
- State class: `MEASUREMENT`
- Updates: Every 1-2 minutes via coordinator

**ShadeRecommendationSensor:**
- Device class: `RUNNING` (or `OPENING` for window context)
- State: `on` (shade recommended) / `off` (no shading)
- Attributes: scenario, reason, all sensor values

---

## Config Flow UI

### Wizard Steps

**Step 1: Welcome**
- Project name input
- Option to use defaults
- Introduction text

**Step 2: Global Sensors**
- Irradiance sensor (required)
- Diffuse irradiance sensor (optional)
- Outdoor temperature (required)
- Indoor temperature (optional)
- Weather warning sensor (optional)
- Weather condition entity (optional)
- Auto-discovery of available sensors

**Step 3: Thresholds**
- Outside temperature threshold (default: 25°C)
- Inside temperature threshold (default: 24°C)
- Forecast high threshold (default: 28°C)
- Solar energy threshold (default: 300 W/m²)
- Slider inputs with validation

**Step 4: Groups (Optional)**
- Create groups?
- Group name
- Indoor temperature override (optional)
- Add more groups option

**Step 5: Add Windows**
- Window name
- Group assignment (multi-select)
- Geometry: width, height, azimuth, tilt, visible azimuth range
- Properties: g-value, frame width, window recess, shading depth
- Add more windows option
- Azimuth help: S=180°, W=270°, N=0°/360°, E=90°

**Step 6: Review & Confirm**
- Summary of all configuration
- Hierarchical display (global → groups → windows)
- Confirmation before creating entry

### UI Features

- Entity selectors with auto-complete
- Multi-select for group assignment
- Range sliders for numeric values
- Help texts and unit displays
- Back/forward navigation
- Progress indicator

---

## Error Handling & Edge Cases

### Graceful Degradation

**Sensor Unavailable:**
- Temperature sensor missing: Skip scenarios requiring it
- Irradiance sensor missing: Log warning, set all energies to 0
- Weather warning sensor missing: Override simply not activated
- Sun entity missing: Critical error (integration should not load)

**Invalid Configuration:**
- Missing required sensors: Config entry error on setup
- Invalid geometry: Log warning, skip window calculation
- Azimuth range invalid (start ≥ end): Log warning
- Sensor doesn't exist in HA: Warning in log, continue

**Calculation Errors:**
- Window calculation fails: Return zero for that window, continue with others
- Coordinator update fails completely: Return last valid data or zeros
- Divide by zero or math errors: Catch and return zero

### State Management

- **Update interval**: 1-2 minutes (configurable)
- **Debouncing**: Don't recalculate on minimal changes (< 5%)
- **Startup**: Immediate calculation after HA start
- **Night mode**: All energies = 0 when sun below horizon

---

## Testing Strategy

### Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures
├── test_coordinator.py            # Solar calculations
├── test_recommendations.py        # Recommendation scenarios
├── test_store.py                  # Configuration storage
├── test_config_flow.py            # Wizard flow
└── test_entities.py               # Entity behavior
```

### Key Test Cases

**Solar Calculations:**
- Clear sky, south-facing window (high direct energy)
- Nighttime (all energies = 0)
- Shading blocks sun (direct = 0, diffuse > 0)
- Cloudy day (high diffuse, low direct)
- Window at edge of visible azimuth range

**Recommendations:**
- Outside temp scenario triggers
- Inside temp scenario triggers
- Forecast scenario triggers
- Seasonal scenario triggers
- Weather warning overrides all scenarios
- No scenario triggers (all off)

**Config Flow:**
- Complete wizard flow
- Skip optional groups
- Skip optional sensors
- Invalid input validation
- Multi-group assignment

**Entities:**
- Window entities update correctly
- Group entities sum correctly
- Global entity sums all
- Attributes populated correctly

### CI/CD Requirements

- Minimum 80% code coverage
- All tests must pass on every PR
- HACS validation must pass
- hassfest validation must pass
- Pre-commit hooks: black, flake8, mypy

---

## CI/CD Pipeline

### GitHub Actions Workflows

**1. ci.yaml** - Main Pipeline
- Trigger: Pull requests, pushes to main
- Steps:
  - Checkout code
  - Set up Python
  - Install dependencies
  - Run black (formatting check)
  - Run flake8 (linting)
  - Run pylint (code quality)
  - Run mypy (type checking)
  - Run pytest with coverage
  - Upload coverage to Codecov

**2. validate.yaml** - HA/HACS Compliance
- Trigger: Pull requests, pushes to main
- Steps:
  - Checkout code
  - Run hassfest (manifest validation)
  - Run hacs-action (HACS requirements)
  - Fail if any validation error

**3. release.yaml** - Automated Releases
- Trigger: Merge to main branch
- Uses: release-please-action
- Steps:
  - Check for release-please PR
  - Create GitHub release
  - Generate CHANGELOG.md
  - Tag version
  - Publish release notes

### Release Process

1. Developer commits changes
2. release-please creates version bump PR
3. PR is reviewed and merged
4. GitHub Action automatically creates release
5. CHANGELOG.md updated
6. Users can update via HACS

### Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-homeassistant]
```

---

## Dependencies

### Python Dependencies (manifest.json)

```json
{
  "domain": "solar_window_system",
  "name": "Solar Window System",
  "version": "1.0.0",
  "documentation": "https://github.com/jmerifjKriwe/solar-window-system",
  "codeowners": ["@jmerifjKriwe"],
  "requirements": [],
  "iot_class": "local_polling"
}
```

**No external dependencies required!**
- Uses built-in `sun.sun` entity
- Uses HA's storage API
- Standard library only

### Home Assistant Version

- **Minimum**: 2026.3
- **Tested against**: 2026.3.x

---

## HACS Compliance

### Required Files

✅ `manifest.json` - With version, requirements, documentation
✅ `hacs.json` - Repository metadata
✅ `README.md` - Installation and configuration
✅ `icon.png` (256×256) - Already present
✅ `icon@2x.png` (512×512) - Already present
✅ `custom_components/solar_window_system/` - Proper directory structure
✅ CI/CD validation - hassfest + hacs-action

### hacs.json

```json
{
  "name": "Solar Window System",
  "content_in_root": false,
  "zip_release": true,
  "filename": "custom_components/solar_window_system.zip",
  "render_readme": true
}
```

---

## Implementation Phases

### Phase 1: Core Foundation
- Project setup (CI/CD, directory structure)
- Basic manifest.json, hacs.json, README.md
- Storage API implementation
- Config flow step 1-3 (global setup)

### Phase 2: Solar Calculations
- Coordinator implementation
- Sun visibility calculation
- Direct radiation calculation
- Diffuse radiation estimation
- Sensor integration with graceful degradation

### Phase 3: Entities
- Window-level sensors (3 energy + 1 recommendation)
- Group-level aggregation
- Global-level aggregation
- Device registry integration

### Phase 4: Recommendations
- All 4 scenarios implemented
- Weather warning override
- Binary sensor with attributes
- Priority logic

### Phase 5: Config Flow Polish
- Groups step (step 4)
- Windows step (step 5)
- Review step (step 6)
- Entity selectors and auto-discovery

### Phase 6: Testing & Refinement
- Comprehensive test suite
- Edge case handling
- Documentation completion
- HACS submission preparation

---

## Success Criteria

✅ Integration loads successfully in Home Assistant 2026.3+
✅ Config flow wizard completes without errors
✅ Solar calculations produce realistic values
✅ Recommendations trigger correctly for all 4 scenarios
✅ Weather warning override works as expected
✅ Entities update every 1-2 minutes
✅ All tests pass with >80% coverage
✅ HACS validation passes (hassfest + hacs-action)
✅ CI/CD pipeline runs successfully on every PR

---

## Future Enhancements (Post v1.0)

- Custom Lovelace card for visualization
- Historical data tracking (statistics)
- Machine learning for optimization
- Integration with actual shading devices (cover control)
- Advanced radiation models (pysolar library)
- Multi-house support
- Energy export calculations

---

## Appendix

### Azimuth Reference

| Direction | Degrees |
|-----------|---------|
| North     | 0° / 360° |
| Northeast | 45° |
| East      | 90° |
| Southeast | 135° |
| South     | 180° |
| Southwest | 225° |
| West      | 270° |
| Northwest | 315° |

### Entity ID Patterns

- Windows: `sensor.solar_window_system.<window_id>_<type>_energy`
- Groups: `sensor.solar_window_system.<group_id>_<type>_energy`
- Global: `sensor.solar_window_system.home_<type>_energy`
- Recommendations: `binary_sensor.solar_window_system.<level>_<id>_shade_recommended`

### Type Values

- `direct` - Direct solar radiation
- `diffuse` - Diffuse solar radiation
- `combined` - Total (direct + diffuse)

---

**Document Version:** 1.0.0
**Last Updated:** 2026-03-03
