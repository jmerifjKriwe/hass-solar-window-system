# Solar Window System

A Home Assistant custom component that calculates solar energy on windows and provides intelligent shading recommendations based on weather conditions, temperature thresholds, and configurable scenarios.

## Features

- **100% UI-Based Configuration**: No YAML required - complete setup through Home Assistant UI
- **Multi-Step Config Flow**: Guided setup with global sensors, groups, and individual windows
- **Hierarchical Structure**: Global → Groups → Windows with inheritance and overrides
- **"Set & Forget" Physical Properties**: Configure geometry once via Config Flow
- **"Tweak & Play" Thresholds**: Adjust thresholds and scenarios dynamically via dashboard entities
- **Shading Recommendations**: Smart "Shading Recommended" binary sensors with 3 scenarios:
  - Inside Temperature: Current indoor comfort levels
  - Outside Temperature: Outdoor conditions  
  - Weather Forecast: Predictive based on forecasted temperatures
- **Weather Override**: Master override via weather warning sensor disables all recommendations
- **Aggregated Readings**: Energy and shading status at window, group, and global levels

## Installation

### Via HACS

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/jmerifjKriwe/solar-window-system`
6. Select "Integration" as the category
7. Click "Add"
8. Search for "Solar Window System" and install it
9. Restart Home Assistant
10. Go to "Settings" > "Devices & Services"
11. Click "Add Integration"
12. Search for "Solar Window System"
13. Follow the configuration wizard

### Manual Installation

1. Copy the `custom_components/solar_window_system` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to "Settings" > "Devices & Services"
4. Click "Add Integration"
5. Search for "Solar Window System"
6. Follow the configuration wizard

## Configuration

### Initial Setup (Config Flow)

1. **Global Setup**: Select required sensors and set default window properties
   - Solar irradiance sensor (required)
   - Outdoor temperature sensor (required)
   - Optional: Indoor temperature, diffuse irradiance, weather warning

2. **Add Groups** (Subentry Flow): Create logical groups
   - Room groups: With indoor temperature sensor
   - Orientation groups: Summary by cardinal direction
   - Group properties can be inherited by windows

3. **Add Windows** (Subentry Flow): Configure each window
   - Geometry: Width, height, azimuth, visible range
   - Properties: g-value, frame width, window recess, shading depth
   - Group assignment for inheritance

### Reconfiguration

Use "Reconfigure" in the integration settings to:
- Change global sensors
- Adjust default properties
- Add/remove groups and windows via subentries

## "Set & Forget" vs "Tweak & Play"

### Set & Forget (Physical Properties)
Configured once via Config Flow:
- **Geometry**: Window size, orientation, visible range
- **Physical Properties**: g-value, frame width, shading depth
- These values rarely change and are stored in the Config Entry

### Tweak & Play (Behavioral Thresholds)
Dynamically adjustable via dashboard entities:
- **Number Entities**: Thresholds for indoor/outdoor temperature, forecast, solar energy
- **Switch Entities**: Toggle the 3 scenarios on/off
- **Button Entities**: Reset overrides per window/group
- Changes are active immediately and persistently saved

## Entities

### Sensor Entities (Power/W)
- `{window} Direct Energy`: Direct solar radiation
- `{window} Diffuse Energy`: Diffuse radiation from the sky
- `{window} Combined Energy`: Total solar heat load
- Group and Global variants for aggregation

### Binary Sensor Entities
- `{window/Group/Global} Shading Recommended`: ON when shading is recommended
  - Icon: mdi:blinds-closed (ON) / mdi:blinds-open (OFF)
  - Device Class: window

### Config Entities (Number)
Thresholds for each window/group/global:
- `Indoor Temperature Threshold`: Trigger for indoor overheating (default: 24°C)
- `Outdoor Temperature Threshold`: Trigger for outdoor conditions (default: 25°C)
- `Forecast Temperature Threshold`: Proactive shading (default: 28°C)
- `Solar Energy Threshold`: Minimum heat load for recommendation (default: 300 W/m²)

### Config Entities (Switch)
Scenario toggles for each window/group/global:
- `Scenario: Indoor Temperature`: Indoor temp check on/off
- `Scenario: Outdoor Temperature`: Outdoor temp check on/off
- `Scenario: Weather Forecast`: Forecast check on/off

### Config Entities (Button)
- `Reset Overrides`: Clears all dynamic overrides, reverts to default values

## Shading Recommendation Logic

### Master Override
Weather warning sensor (optional): When ON, **all** shading recommendations are suppressed.

### Scenario Logic (OR combination)
Shading is recommended when:
1. **Indoor Temperature Scenario** ACTIVE: `indoor_temp > threshold_indoor`
2. **Outdoor Temperature Scenario** ACTIVE: `outdoor_temp > threshold_outdoor`
3. **Forecast Scenario** ACTIVE: `forecast_high > threshold_forecast` AND `indoor_temp > threshold_forecast - 2`

**AND** at least one scenario triggers **AND** `solar_energy > threshold_radiation`

### Inheritance
- Window overrides have priority
- If not set: Group values
- If not set: Global defaults
- Button "Reset Overrides" clears Window/Group overrides

## Development

### DevContainer (Recommended)

The easiest way to develop is using the VS Code DevContainer:

1. Open the project in VS Code
2. Press `F1` → "Dev Containers: Reopen in Container"
3. Wait for the container to build (~2-3 minutes)
4. Run `scripts/start-ha.sh` to start Home Assistant
5. Open http://localhost:8123

See `.devcontainer/README.md` for details.

### Local Development

Alternatively, you can develop locally with:
- Python 3.14+
- See `scripts/README.md` for setup instructions

## License

MIT License - see LICENSE file for details
