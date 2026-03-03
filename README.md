# Solar Window System

A Home Assistant custom component that calculates solar energy on windows and provides intelligent recommendations for opening/closing windows based on weather conditions, seasons, and temperature.

## Features

- **Solar Energy Calculation**: Calculate solar energy on windows based on orientation and weather
- **Hierarchical Configuration**: Configure sensors, thresholds, groups, and windows in a structured way
- **Four Recommendation Scenarios**:
  - Seasonal: Time of year (winter/summer)
  - Weather Forecast: Sunny vs. cloudy days
  - Inside Temperature: Current indoor comfort levels
  - Outside Temperature: Outdoor conditions
- **Aggregated Readings**: Combine readings from multiple windows
- **Weather Override**: Override recommendations based on current weather conditions

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

The integration uses a hierarchical configuration structure:

### Sensors
Configure temperature and weather sensors to use for calculations.

### Thresholds
Set temperature thresholds for different scenarios:
- Summer/winter temperature ranges
- Inside/outside temperature triggers

### Groups
Organize windows into logical groups (e.g., by room or floor).

### Windows
Configure individual windows with:
- Orientation (N, S, E, W, NE, NW, SE, SW)
- Area (in square meters)
- Group assignment
- Associated sensors

## Entities

The integration creates the following entities:

### Energy Sensors
- `sensor.{window}_solar_energy`: Calculated solar energy for each window
- `sensor.{group}_solar_energy`: Aggregated solar energy for each group
- `sensor.total_solar_energy`: Total solar energy across all windows

### Recommendation Sensors
- `sensor.{window}_recommendation`: Open/close recommendation for each window
- `sensor.{group}_recommendation`: Aggregated recommendation for each group
- `sensor.system_recommendation`: Overall system recommendation

## Recommendation Scenarios

### 1. Seasonal
- **Winter**: Recommend closing windows during sunny hours to retain heat
- **Summer**: Recommend opening windows during cool hours, closing during peak sun

### 2. Weather Forecast
- **Sunny**: Adjust recommendations based on forecasted solar gain
- **Cloudy**: Allow more ventilation as solar heating is reduced

### 3. Inside Temperature
- **Too Hot**: Recommend opening windows for cooling
- **Too Cold**: Recommend closing windows to retain heat
- **Comfortable**: Maintain current state

### 4. Outside Temperature
- **Moderate**: Favor open windows for ventilation
- **Extreme**: Recommend closing windows

## License

MIT License - see LICENSE file for details
