# Solar Window System - User Guide

## What Does This Do?

The Solar Window System calculates how much solar energy is hitting your windows and tells you when to close the blinds to keep your home cool.

**It answers:**
- "How much sun is coming through my south window right now?"
- "Should I close the blinds to keep the bedroom cool?"
- "What's the total solar energy gain for my entire house?"

## How It Works

### The Physics

**Direct Solar Radiation:**
Sun hits your window directly. The amount depends on:
- Sun angle (high sun = more energy)
- Window direction (south-facing gets more)
- Window size (bigger windows = more energy)
- Glass type (g-value determines how much passes through)

**Diffuse Solar Radiation:**
Sunlight scattered by the atmosphere (clouds, haze). This comes from all directions.

**Shading:**
Roof overhangs, balconies, and awnings block the sun when it's low in the sky.

### What the System Calculates

For each window, every 2 minutes:
1. Checks sun position (elevation, azimuth)
2. Reads weather sensors (irradiance, temperature)
3. Estimates diffuse radiation based on weather
4. Calculates direct energy through the glass
5. Adds window shading effects
6. Aggregates by room and whole-house

## Installation

### Prerequisites

- Home Assistant 2026.3 or newer
- Weather station or solar irradiance sensor
- Temperature sensors (indoor and/or outdoor)

### Step 1: Install the Integration

**Via HACS (when published):**
1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Search for "Solar Window System"
4. Click "Install"
5. Restart Home Assistant

**Manually:**
1. Copy `custom_components/solar_window_system/` to your HA config
2. Restart Home Assistant

### Step 2: Add the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Solar Window System"
4. Follow the setup wizard

### Step 3: Configure Global Settings

**Required Sensors:**
- **Solar Radiation:** Your weather station's irradiance sensor (W/m²)
- **Outdoor Temperature:** Temperature sensor outside (°C)

**Optional Sensors:**
- **Diffuse Radiation:** Direct diffuse sensor (if available)
- **Indoor Temperature:** Room temperature sensor
- **Weather Warning:** Weather alert binary sensor
- **Weather Condition:** Current condition (sunny, cloudy, etc.)

**Thresholds:**
- **Outside Temperature:** When to start considering shading (default: 25°C)
- **Solar Energy:** Energy threshold for recommendations (default: 300 W/m²)

### Step 4: Configure Your Windows

**Geometry (Required):**
- **Name:** e.g., "Living Room South Window"
- **Width:** Window width in cm
- **Height:** Window height in cm
- **Azimuth:** Direction window faces (South=180°, West=270°, North=0°, East=90°)
- **Azimuth Range:** Sun angles when window is visible (e.g., South window: 150° to 210°)
- **Tilt:** Usually 90° (vertical windows)

**Properties (Optional):**
- **G-value:** Solar heat gain coefficient (default: 0.6)
  - Single glass: ~0.85
  - Double glazing: ~0.70
  - Low-E glass: ~0.50-0.60
  - Triple glazing: ~0.50
- **Frame Width:** Frame width in cm (reduces glass area)
- **Window Recess:** How far back the window is from wall (cm)
- **Shading Depth:** Roof overhang or balcony depth (cm)

### Step 5: Create Groups (Optional)

Group windows by:
- **Room:** "Bedroom", "Kitchen", etc.
- **Orientation:** "South-facing", "West-facing"
- **Floor:** "Second floor", "Ground floor"

Benefits:
- See total energy per room
- Automate shading by room
- Simplify dashboards

## Understanding the Sensors

### Energy Sensors

For each window, you get 3 sensors:

**`sensor.solar_window_system.{window}_direct_energy`**
- Direct solar radiation through the window
- What you feel when sun hits you
- Measured in Watts (W)

**`sensor.solar_window_system.{window}_diffuse_energy`**
- Diffuse/scattered radiation
- Present even when sun isn't directly hitting window
- Measured in Watts (W)

**`sensor.solar_window_system.{window}_combined_energy`**
- Total solar energy (direct + diffuse)
- Use this for automation
- Measured in Watts (W)

### Group Sensors

If you create groups, you also get:

**`sensor.solar_window_system.{group}_direct_energy`**
- Sum of direct energy for all windows in group

**`sensor.solar_window_system.{group}_combined_energy`**
- Total energy for the room/orientation

### Global Sensors

**`sensor.solar_window_system.home_direct_energy`**
- Total direct solar energy for entire house

**`sensor.solar_window_system.home_combined_energy`**
- Total solar energy hitting all windows

## Example Values

### Sunny Day, South Window

```
Direct Energy:      450 W
Diffuse Energy:      100 W
Combined Energy:     550 W
```

### Cloudy Day, Same Window

```
Direct Energy:        50 W
Diffuse Energy:      200 W
Combined Energy:      250 W
```

### Night

```
Direct Energy:        0 W
Diffuse Energy:        0 W
Combined Energy:       0 W
```

## Using the Data

### Automation Examples

**Close blinds when too much sun:**
```yaml
alias:
  - id: close_south_blinds
    trigger:
      - platform: numeric_state
        entity_id: sensor.solar_window_system.living_room_south_combined_energy
        above: 400
    action:
      - service: cover.close_cover
        entity_id: cover.living_room_south_blind
```

**Close bedroom blinds during hot afternoon:**
```yaml
alias:
  - id: close_bedroom_blinds_hot_afternoon
    trigger:
      - platform: state
        entity_id: sun.sun
        to: "above_horizon"
      - platform: numeric_state
        entity_id: sensor.weather_temperature
        above: 28
      - platform: template
        value_template: "{{ now().hour >= 14 and now().hour <= 18 }}"
    condition:
      - condition: numeric_state
        entity_id: sensor.solar_window_system.bedroom_combined_energy
        above: 300
    action:
      - service: cover.close_cover
        entity_id: cover.bedroom_blinds
```

**Track daily solar energy:**
```yaml
utility_meter:
  daily_solar_energy:
    source: sensor.solar_window_system.home_combined_energy
    cycle: daily
```

### Dashboard Examples

**Room Energy Card:**
```yaml
type: entities
  entities:
    - entity: sensor.solar_window_system.living_room_combined_energy
      name: Living Room
      icon: mdi:sun-wireless
    - entity: sensor.solar_window_system.kitchen_combined_energy
      name: Kitchen
      icon: mdi:sun-wireless
    - entity: sensor.solar_window_system.bedroom_combined_energy
      name: Bedroom
      icon: mdi:sun-wireless
  title: Solar Energy by Room
```

**Individual Window Detail:**
```yaml
type: glance
  entities:
    - entity: sensor.solar_window_system.living_room_south_direct_energy
      name: Direct
    - entity: sensor.solar_window_system.living_room_south_diffuse_energy
      name: Diffuse
    - entity: sensor.solar_window_system.living_room_south_combined_energy
      name: Total
  title: Living Room South Window
```

## Troubleshooting

### Sensors Show 0

**Check:**
1. Is it night? Sun below horizon = 0 energy
2. Is weather sensor reporting? Check `sensor.{your_irradiance_sensor}`
3. Is window geometry correct? Azimuth range matters!

### Sensors Show "Unknown"

**Check:**
1. Did HA just restart? Wait 2 minutes for first update
2. Check Configuration → Integrations → Solar Window System
3. Look at Home Assistant logs for errors

### Values Seem Wrong

**Check:**
1. Window azimuth: South=180°, East=90°, West=270°, North=0°
2. G-value: Lower g-value = less energy passes through
3. Frame width: Larger frame = smaller glass area

### Sensor Not Updating

**Check:**
1. Update interval is 2 minutes (default)
2. Check sun position - is it above horizon?
3. Verify weather sensors are updating

## Advanced Configuration

### G-Value Guide

The g-value (solar heat gain coefficient) determines how much solar energy passes through your glass:

**Window Type | G-Value**
------------|---------
Single clear glass | 0.85 - 0.90
Double clear glazing | 0.70 - 0.75
Double low-E coating | 0.60 - 0.70
Triple glazing | 0.50 - 0.60

**Find your g-value:**
- Check window specifications
- Look for "SHGC" or "g-value" in documentation
- When in doubt, use default (0.6)

### Azimuth Guide

**Direction to Degrees:**
- South: 180°
- Southeast: 135°
- East: 90°
- Northeast: 45°
- North: 0°
- Northwest: 315°
- West: 270°
- Southwest: 225°

**Visible Azimuth Range:**
- For a south-facing window (180°), the sun is visible when it's roughly south
- Set range to 150°-210° for main sun exposure
- Wider range = longer sun exposure but less accurate

### Shading Depth

**Calculate overhang/blockage:**
1. Measure distance from window to outer edge of shading (cm)
2. This is your shading_depth

**Example:**
- 100 cm roof overhang
- 30 cm window recess (window set back from wall)
- System blocks sun when elevation is below ~17°

## Performance Tips

### Update Interval

Default: 2 minutes

**Faster updates (more accurate):**
- Change to 60 seconds in configuration
- Uses more HA resources

**Slower updates (less CPU):**
- Change to 5 minutes
- Misses rapid sun position changes

### Number of Windows

**Small system (1-10 windows):** No performance impact
**Medium system (10-30 windows):** Still fast
**Large system (30+ windows):** Consider grouping by floor/orientation

## Getting Help

### Debug Mode

Enable logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.solar_window_system: debug
```

### Check System Status

**Developer Tools → States:**
- Find `sun.sun` - verify sun position
- Check weather sensors - verify they're updating
- Look at solar sensors - see current values

**Developer Tools → YAML:**
```yaml
{{ state_attr('sun.sun', 'elevation') }}
{{ state_attr('sun.sun', 'azimuth') }}
{{ states('sensor.solar_window_system') }}
```

## Common Use Cases

### Automatic Blinds Control

Close south-facing blinds when solar energy > 500 W:

```yaml
automation:
  - alias: "Solar powered blind control"
    trigger:
      - platform: numeric_state
        entity_id: sensor.solar_window_system.living_room_south_combined_energy
        above: 500
    action:
      - service: cover.close_cover
        target:
          entity_id: cover.living_room_south
    condition:
      - condition: state
        entity_id: sun.sun
        state: "above_horizon"
```

### Energy Monitoring

Track how much solar energy enters your home:

```yaml
sensor:
  - platform: template
    sensors:
      daily_solar_gain:
        friendly_name: "Daily Solar Energy Gain"
        unit_of_measurement: "kWh"
        device_class: energy
        state_class: total_increasing
        attributes:
          last_reset:
          - trigger:
              - platform: time
                at: "00:00:00"
            - sensor.reset_daily
        state: >
          {% set total = states('sensor.solar_window_system.home_combined_energy') | float(0) %}
          {% set kwh = total / 1000 %}
          {{ kwh | round(2) }}
```

### Room-by-Room Control

Different thresholds per room:

```yaml
automation:
  - alias: "Bedroom solar limit"
    trigger:
      - platform: numeric_state
        entity_id: sensor.solar_window_system.bedroom_combined_energy
        above: 200  # Lower threshold for bedroom
    action:
      - service: cover.close_cover
        entity_id: cover.bedroom_blind

  - alias: "Kitchen solar limit"
    trigger:
      - platform: numeric_state
        entity_id: sensor.solar_window_system.kitchen_combined_energy
        above: 600  # Higher threshold for kitchen
    action:
      - service: cover.close_cover
        entity_id: cover.kitchen_blind
```

## FAQ

**Q: Why are my sensors showing 0?**
A: Check if it's night (sun below horizon). Solar energy is 0 at night.

**Q: The values seem too high/low.**
A: Check your g-value and frame width. Double-glazed windows (g=0.6) let in less energy than single-pane (g=0.85).

**Q: Can I use this with skylights?**
A: Yes! Just set tilt to 0° (horizontal) and adjust geometry accordingly.

**Q: Does this work with shading from trees?**
A: The system calculates roof/balcony shading. Tree shading would need manual overrides or external sensors.

**Q: How accurate is this?**
A: As accurate as your weather sensors. The physics models are based on standard solar radiation equations used in building engineering.

**Q: Can I calibrate this?**
A: Adjust g-value to match your actual windows. Compare sensor readings with a pyranometer if you have one.

**Q: What's the difference between g-value and SHGC?**
A: They're similar! G-value is the European term, SHGC is the North American term. Both measure solar heat gain through glass (0-1 scale).

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/jmerifjKriwe/solar-window-system
- Documentation: See `docs/` folder
- Home Assistant Community: https://community.home-assistant.io/

Enjoy your smarter solar-powered home! ☀️
