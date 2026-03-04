# Solar Window System - Quick Reference

## At a Glance

**What it does:** Calculates solar energy through windows, recommends shading
**Update frequency:** Every 2 minutes
**Entities created:** 3 per window (direct, diffuse, combined energy)
**Test coverage:** 38 tests, 100% passing

## Entity Naming Pattern

### Window Level
```
sensor.solar_window_system.{window_name}_{energy_type}_energy

Examples:
  sensor.solar_window_system.living_room_south_direct_energy
  sensor.solar_window_system.bedroom_east_diffuse_energy
  sensor.solar_window_system.kitchen_west_combined_energy
```

### Group Level
```
sensor.solar_window_system.{group_name}_{energy_type}_energy

Examples:
  sensor.solar_window_system.ground_floor_direct_energy
  sensor.solar_window_system.south_facing_diffuse_energy
  sensor.solar_window_system.bedrooms_combined_energy
```

### Global Level
```
sensor.solar_window_system.home_{energy_type}_energy

Examples:
  sensor.solar_window_system.home_direct_energy
  sensor.solar_window_system.home_diffuse_energy
  sensor.solar_window_system.home_combined_energy
```

## Configuration Hierarchy

```
Global (sensors, thresholds, defaults)
  ├── Groups (optional - rooms, orientations)
  │   ├── Group A windows
  │   └── Group B windows
  └── Windows (individual)
      ├── Window 1 (geometry, properties)
      ├── Window 2 (geometry, properties)
      └── Window 3 (geometry, properties)
```

## Key Constants

**Thresholds:**
- Outside temp: 25°C (when to consider shading)
- Inside temp: 24°C (comfort threshold)
- Solar energy: 300 W/m² (energy threshold)
- Update interval: 120 seconds (2 minutes)

**Property Defaults:**
- G-value: 0.6 (solar heat gain coefficient)
- Frame width: 10 cm
- Window recess: 0 cm
- Shading depth: 0 cm

**Azimuth Guide:**
- South: 180°
- West: 270°
- North: 0°
- East: 90°

## Energy Types Explained

| Type | Description | When It's Zero |
|------|-------------|----------------|
| **Direct** | Sun hitting window directly | Night, blocked by shade, wrong azimuth |
| **Diffuse** | Scattered light (clouds, sky) | Never (always some diffuse) |
| **Combined** | Direct + Diffuse | Night only |

## Solar Angle Trigonometry

**Incidence Factor:**
```
cos(|sun_azimuth - window_azimuth|)

Perfect (sun directly facing): cos(0°) = 1.0 (100%)
Oblique (45° off): cos(45°) = 0.707 (70.7%)
Grazing (90° off): cos(90°) = 0 (0%)
```

**Shade Angle:**
```
atan2(window_recess + 1, shading_depth)

Large overhang: High shade angle (blocks more)
No overhang: 0° shade angle (blocks nothing)
```

## Typical Values

### Sunny Day, South Window
```
Irradiance: 800 W/m²
Elevation: 45° (sun halfway up)
Azimuth: 180° (south)

Results:
  Direct: 400-500 W
  Diffuse: 80-150 W
  Combined: 480-650 W
```

### Cloudy Day
```
Irradiance: 400 W/m²
Weather: cloudy

Results:
  Direct: 50-100 W
  Diffuse: 250-350 W
  Combined: 300-450 W
```

### Night
```
Sun: Below horizon

Results:
  Direct: 0 W
  Diffuse: 0 W
  Combined: 0 W
```

## Automation Templates

### Basic Shading Trigger
```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.solar_window_system.{window}_combined_energy
    above: 400  # Adjust to your preference
```

### Time-Restricted Shading
```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.solar_window_system.{window}_combined_energy
    above: 400
condition:
  - condition: time
    after: "10:00:00"
    before: "18:00:00"
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
```

### Multi-Condition Shading
```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.solar_window_system.{window}_combined_energy
    above: 400
condition:
  - condition: numeric_state
    entity_id: sensor.temperature_outside
    above: 25  # Only when hot outside
  - condition: state
    entity_id: sun.sun
    state: "above_horizon"  # Only during day
```

## Dashboard Snippets

### Energy Card (Lovelace)
```yaml
type: energy-card
entity: sensor.solar_window_system.living_room_south_combined_energy
```

### Gauge Card (Lovelace)
```yaml
type: gauge
entity: sensor.solar_window_system.living_room_south_combined_energy
min: 0
max: 1000
name: Solar Energy
```

### Bar Chart (History Graph)
```yaml
type: custom:bar-card
entities:
  - entity: sensor.solar_window_system.living_room_south_direct_energy
    name: Direct
  - entity: sensor.solar_window_system.living_room_south_diffuse_energy
    name: Diffuse
```

## Debugging Commands

### Check Current Values
```yaml
{{ state_attr('sun.sun', 'elevation') }}
{{ state_attr('sun.sun', 'azimuth') }}
{{ states('sensor.solar_window_system') }}
```

### Find All Solar Sensors
```bash
# In HA terminal
states('sensor.solar_window_system')
```

### Test Sensor Reading
```yaml
{{ state_attr('sensor.solar_window_system.living_room_south_direct_energy', 'last_updated') }}
{{ state_attr('sensor.solar_window_system.living_room_south_direct_energy', 'device_class') }}
```

## Performance Benchmarks

| Metric | Value |
|--------|-------|
| Test suite runtime | 0.28s (38 tests) |
| Update cycle | 2 minutes (configurable) |
| Per window calculation | ~5-10ms |
| Memory usage | <1MB (config) |
| CPU usage | Negligible |

## File Structure Reference

```
custom_components/solar_window_system/
├── __init__.py          # Entry point, async_setup_entry
├── const.py             # All constants (43 total)
├── coordinator.py       # Calculation engine (9 methods)
├── sensor.py            # HA sensor entities
└── store.py             # Config persistence

tests/
├── conftest.py          # Test fixtures
├── test_const.py        # 3 tests
├── test_coordinator.py  # 21 tests
├── test_sensor.py       # 11 tests
└── test_store.py        # 3 tests
```

## Common G-Values

| Window Type | G-Value | Use This When |
|-------------|---------|---------------|
| Single clear glass | 0.85 | Old windows |
| Double clear glazing | 0.75 | Standard double-pane |
| Double low-E coating | 0.63 | Modern energy-efficient |
| Triple glazing, low-E | 0.50 | High-performance windows |

## Azimuth Quick Reference

| Direction | Degrees | Visible Range Example |
|-----------|---------|----------------------|
| North | 0 | 315-45 (wide) or 0-45 (narrow) |
| Northeast | 45 | 0-90 |
| East | 90 | 45-135 |
| Southeast | 135 | 90-180 |
| South | 180 | 135-225 |
| Southwest | 225 | 180-270 |
| West | 270 | 225-315 |
| Northwest | 315 | 270-360/0-45 |

**Pro Tip:** For a south-facing window (180°), use 150-210° range to capture midday sun without early morning/late evening angles.

## Update Intervals

| Interval | Use Case |
|----------|----------|
| 30 seconds | Testing, rapid changes |
| 60 seconds | Accurate tracking |
| 120 seconds (default) | Balanced |
| 300 seconds | Low CPU |
| 600 seconds | Minimal updates |

## Troubleshooting Checklist

- [ ] Is it night? (Sun below horizon = 0 energy)
- [ ] Is weather sensor updating?
- [ ] Is window azimuth correct? (South=180°)
- [ ] Is g-value set correctly? (0.5-0.8 typical)
- [ ] Check visible azimuth range - too narrow?
- [ ] Verify frame width isn't too large
- [ ] Is update interval acceptable?
- [ ] Check HA logs for errors

## Repository Links

- **GitHub:** https://github.com/jmerifjKriwe/solar-window-system
- **Documentation:** `docs/` folder
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions

## Version History

- **v1.0.0** (March 2026): Initial release
  - Solar energy calculation
  - Window/group/global aggregation
  - 38 passing tests
  - Full documentation

---

**Remember:** Solar energy calculations are physics-based estimates. Real-world performance depends on weather, atmospheric conditions, and actual window properties. Use the calculated values as guidelines, not absolute truths.
