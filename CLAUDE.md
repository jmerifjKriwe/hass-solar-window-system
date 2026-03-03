# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom component for a solar window system. The component integrates with Home Assistant to provide control and automation for solar-powered window treatments or similar devices.

## Project Structure

This project follows the standard Home Assistant custom component structure:

```
solar_window_system/
├── icon.png (256x256)
├── icon@2x.png (512x512)
├── custom_components/
│   └── solar_window_system/
│       ├── __init__.py
│       ├── manifest.json
│       ├── strings.json
│       └── [component files]
└── CLAUDE.md
```

## Development Commands

### Home Assistant Development
- Home Assistant configuration: `/homeassistant/config/`
- Restart Home Assistant: `hassio homeassistant restart` (via Supervisor) or restart from UI
- Check logs: Settings > System > Logs in Home Assistant UI, or `/homeassistant/config/home-assistant.log`
- Configuration validation: Settings > System > Checks in Home Assistant UI

### Python Development
- Format code: `black .`
- Lint: `flake8` or `pylint`
- Type checking: `mypy .`
- Run tests: `pytest tests/`

### Testing
- Home Assistant provides `pytest-homeassistant-custom-component` for testing custom components
- Test file structure: `tests/test_*.py`
- Mock Home Assistant core: Use `pytest` fixtures from `homeassistant`

## Architecture

### Component Types
Home Assistant custom components can extend several platform types:
- **sensor**: Provide data readings (temperature, power, status)
- **binary_sensor**: On/off state detection
- **switch**: Control on/off functionality
- **cover**: Window treatments, blinds, shades
- **climate**: Temperature control systems

### Core Components
- **manifest.json**: Component metadata (version, requirements, documentation)
- **__init__.py**: Component setup and async_setup_entry
- **strings.json**: UI strings for translations
- **entity.py**: Base entity class with shared functionality
- **[platform].py**: Platform-specific implementations (sensor.py, switch.py, etc.)

### Key Patterns
- Use `async`/`await` for all I/O operations
- Store API clients in `config_entries` with `entry.runtime_data`
- Use `CoordinatorEntity` from `homeassistant.helpers.update_coordinator` for data polling
- Implement `async_update` for entity state updates
- Use Home Assistant's built-in device registry via `async_get_registry` for device tracking

### Config Flow
- Implement `config_flow.py` for UI-based configuration
- Use `FlowHandler` with `async_step_user` and `async_step_form`
- Store configuration in `config_entries`
- Validate user input before creating config entry

### Services
- Define services in `services.yaml`
- Register services in `async_setup`
- Implement service handlers as async methods

## File Naming Conventions
- Use lowercase with underscores: `solar_window_controller.py`
- Platform files: `[platform].py` (e.g., `sensor.py`, `switch.py`)
- Test files: `test_[filename].py`

## HACS Integration
This component is designed for HACS (Home Assistant Community Store):
- Icons follow HACS size requirements (256x256 and 512x512)
- manifest.json should include HACS-specific fields
- Submit to HACS: https://hacs.xyz/docs/publish/include
