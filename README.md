# Solar Window System – Home Assistant Custom Component

## Overview

The Solar Window System is a Home Assistant custom component that calculates when window shading is recommended based on solar radiation, temperature, and weather conditions. It provides sensors and binary sensors to inform your automations, but **does not control window shading directly**—you must create your own automations using the provided entities.

## Features

- **Sensor-based Recommendations**: Calculates and exposes when shading is recommended for each window.
- **Multiple Scenarios**: Supports logic for strong sun, diffuse heat, and heatwave forecasts (Scenarios A, B, C).
- **Configurable Presets**: Choose between Normal, Relaxed, Sensitive, Children, or Custom modes to adjust sensitivity and behavior.
- **Flexible Configuration**: YAML-based group and window configuration, plus UI-based options for tuning.
- **Entities for Automations**: Exposes sensors, binary sensors, numbers, switches, and selects for use in your own automations.

## Installation

### Manual
1. Copy the `custom_components/solar_window_system` folder to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration via the Home Assistant UI.

### HACS (Home Assistant Community Store)
1. In HACS, go to "Integrations" > "Custom Repositories" and add the repository URL of this project as a custom integration.
2. Search for "Solar Window System" in HACS and install it.
3. Restart Home Assistant and add the integration via the UI.

## Usage Warning

> **Note:** This integration only provides sensors and binary sensors that indicate when shading is recommended. **You must create your own automations** (e.g., with Home Assistant Automations or Scripts) to actually control your window shading devices.

## Configuration

### 1. YAML Structure

#### `windows.yaml`
Defines each window and its properties:

```yaml
windows:
  eg_atelier_sued:
    name: "EG Atelier - Süd"
    azimuth: 208
    azimuth_range: [-84, 90]
    elevation_range: [20, 90]
    width: 1.170
    height: 1.250
    shadow_depth: 0.15
    shadow_offset: 0
    room_temp_entity: "sensor.temperatur_wohnzimmer"
    group_type: "atelier"
    # ...
```

#### `groups.yaml`
Defines group defaults for thresholds and scenarios:

```yaml
groups:
  atelier:
    name: "Atelier/Büro"
    thresholds:
      direct: 200
      diffuse: 150
    temperatures:
      indoor_base: 23.0
      outdoor_base: 19.5
    scenario_b:
      enabled: true
      temp_indoor_offset: 0.0
      temp_outdoor_offset: 6.0
    scenario_c:
      enabled: true
      temp_forecast_threshold: 28.5
      start_hour: 9
    # ...
```

### 2. Options Flow
After adding the integration, use the options flow in the UI to select sensors, set update intervals, and adjust scenario parameters.

### 3. Presets and Tuning
Select or customize preset modes (Normal, Relaxed, Sensitive, Children, Custom) to fit your needs. Adjust number entities for fine-tuning.

## Entities

### Sensors
- `sensor.solar_window_power_*`: Solar power per window (W)
- `sensor.solar_window_summary`: Total power, window count, shading count

### Binary Sensors
- `binary_sensor.solar_window_shading_*`: Indicates if shading is recommended for each window

### Numbers
- Adjustable parameters: global sensitivity, children factor, temperature offset, g-value, frame width, diffuse factor, tilt, thresholds, scenario offsets, etc.

### Switches
- Maintenance mode, debug mode, scenario toggles

### Select
- Preset mode selection (Normal, Relaxed, Sensitive, Children, Custom)

## Advanced

- **Group/Window Overrides**: Fine-tune thresholds and physical properties per group or window via YAML.
- **Debugging**: Enable debug mode for detailed logging.
- **Maintenance Mode**: Pause recommendations for cleaning or repairs.

## Example Automation

```yaml
automation:
  - alias: "Shade window when recommended"
    trigger:
      - platform: state
        entity_id: binary_sensor.solar_window_shading_eg_atelier_sued
        to: 'on'
    action:
      - service: cover.close_cover
        target:
          entity_id: cover.your_window_cover
```

## License

See LICENSE file.