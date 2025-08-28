"""Tests for __init__.py module."""

import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.solar_window_system.const import DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


class TestInitSetup:
    """Test the main setup functions in __init__.py."""

    @pytest.fixture
    def mock_hass(self) -> HomeAssistant:
        """Create a mock Home Assistant instance."""
        hass = Mock(spec=HomeAssistant)
        hass.config_entries = Mock()
        hass.config_entries.async_entries = Mock(return_value=[])
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        hass.config_entries.async_unload_platforms = AsyncMock()
        hass.services = Mock()
        hass.services.has_service = Mock(return_value=False)
        hass.services.async_register = Mock()
        hass.data = {}
        # Add config attribute for device registry
        hass.config = Mock()
        hass.config.config_dir = tempfile.mkdtemp()
        return hass

    @pytest.fixture
    def mock_entry_global(self) -> ConfigEntry:
        """Create a mock global config entry."""
        entry = Mock(spec=ConfigEntry)
        entry.title = "Solar Window System"
        entry.entry_id = "global_config_entry_id"
        entry.data = {"entry_type": "global_config"}
        entry.options = {"update_interval": 5}
        entry.subentries = None
        entry.add_update_listener = Mock()
        return entry

    @pytest.fixture
    def mock_entry_group_configs(self) -> ConfigEntry:
        """Create a mock group configs entry."""
        entry = Mock(spec=ConfigEntry)
        entry.title = "Group Configurations"
        entry.entry_id = "group_configs_entry_id"
        entry.data = {"entry_type": "group_configs"}
        entry.options = {}
        entry.subentries = {}
        entry.add_update_listener = Mock()
        return entry

    @pytest.fixture
    def mock_entry_window_configs(self) -> ConfigEntry:
        """Create a mock window configs entry."""
        entry = Mock(spec=ConfigEntry)
        entry.title = "Window Configurations"
        entry.entry_id = "window_configs_entry_id"
        entry.data = {"entry_type": "window_configs"}
        entry.options = {}
        entry.subentries = {}
        entry.add_update_listener = Mock()
        return entry

    @pytest.mark.asyncio
    async def test_async_setup_entry_global_config(
        self, mock_hass: HomeAssistant, mock_entry_global: ConfigEntry
    ) -> None:
        """Test setup for global config entry."""
        # Mock device registry
        mock_device_registry = Mock()
        mock_device_registry.async_get_or_create = Mock()

        with patch(
            "custom_components.solar_window_system.dr.async_get",
            return_value=mock_device_registry,
        ):
            result = await self._call_async_setup_entry(mock_hass, mock_entry_global)

            assert result is True
            mock_device_registry.async_get_or_create.assert_called_once()
            mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
                mock_entry_global, ["sensor", "number", "text", "select", "switch"]
            )

    @pytest.mark.asyncio
    async def test_async_setup_entry_group_configs(
        self, mock_hass: HomeAssistant, mock_entry_group_configs: ConfigEntry
    ) -> None:
        """Test setup for group configs entry."""
        # Mock coordinator
        mock_coordinator = Mock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        with (
            patch(
                "custom_components.solar_window_system.SolarWindowSystemCoordinator",
                return_value=mock_coordinator,
            ),
            patch(
                "custom_components.solar_window_system._create_subentry_devices"
            ) as mock_create_devices,
        ):
            result = await self._call_async_setup_entry(
                mock_hass, mock_entry_group_configs
            )

            assert result is True
            mock_create_devices.assert_called_once_with(
                mock_hass, mock_entry_group_configs
            )
            mock_coordinator.async_config_entry_first_refresh.assert_called_once()
            mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
                mock_entry_group_configs, ["select", "sensor"]
            )
            mock_entry_group_configs.add_update_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_setup_entry_window_configs(
        self, mock_hass: HomeAssistant, mock_entry_window_configs: ConfigEntry
    ) -> None:
        """Test setup for window configs entry."""
        # Mock coordinator
        mock_coordinator = Mock()
        mock_coordinator.async_config_entry_first_refresh = AsyncMock()

        with (
            patch(
                "custom_components.solar_window_system.SolarWindowSystemCoordinator",
                return_value=mock_coordinator,
            ),
            patch(
                "custom_components.solar_window_system._create_subentry_devices"
            ) as mock_create_devices,
        ):
            result = await self._call_async_setup_entry(
                mock_hass, mock_entry_window_configs
            )

            assert result is True
            mock_create_devices.assert_called_once_with(
                mock_hass, mock_entry_window_configs
            )
            mock_coordinator.async_config_entry_first_refresh.assert_called_once()
            mock_hass.config_entries.async_forward_entry_setups.assert_called_once_with(
                mock_entry_window_configs,
                ["select", "sensor", "binary_sensor", "number", "text", "switch"],
            )
            mock_entry_window_configs.add_update_listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_registration_recalculate(
        self, mock_hass: HomeAssistant, mock_entry_global: ConfigEntry
    ) -> None:
        """Test that recalculate service is registered only once."""
        # Mock device registry
        mock_device_registry = Mock()
        mock_device_registry.devices = Mock()
        mock_device_registry.devices.get_entry = Mock(return_value=None)
        mock_device_registry.async_get_or_create = Mock()

        with patch(
            "custom_components.solar_window_system.dr.async_get",
            return_value=mock_device_registry,
        ):
            # First call should register the service
            await self._call_async_setup_entry(mock_hass, mock_entry_global)

            # Verify service was registered
            mock_hass.services.async_register.assert_called()
            assert len(mock_hass.services.async_register.call_args_list) > 0

            # Find the recalculate service registration
            recalculate_call = None
            for call in mock_hass.services.async_register.call_args_list:
                if (
                    len(call[0]) >= 2
                    and call[0][1] == "solar_window_system_recalculate"
                ):
                    recalculate_call = call
                    break

            assert recalculate_call is not None

            # Reset mock for second call
            mock_hass.services.async_register.reset_mock()
            mock_hass.services.has_service.return_value = True

            # Second call should not register again
            await self._call_async_setup_entry(mock_hass, mock_entry_global)

            # Verify service was not registered again
            assert mock_hass.services.async_register.call_count == 0

    @pytest.mark.asyncio
    async def test_service_registration_create_subentry_devices(
        self, mock_hass: HomeAssistant, mock_entry_global: ConfigEntry
    ) -> None:
        """Test that create_subentry_devices service is registered only once."""
        mock_hass.services.has_service.return_value = False

        # Mock device registry
        mock_device_registry = Mock()
        mock_device_registry.devices = Mock()
        mock_device_registry.devices.get_entry = Mock(return_value=None)
        mock_device_registry.async_get_or_create = Mock()

        with patch(
            "custom_components.solar_window_system.dr.async_get",
            return_value=mock_device_registry,
        ):
            await self._call_async_setup_entry(mock_hass, mock_entry_global)

        # Verify service was registered
        mock_hass.services.async_register.assert_called()
        assert len(mock_hass.services.async_register.call_args_list) > 0

        # Find the create_subentry_devices service registration
        create_devices_call = None
        for call in mock_hass.services.async_register.call_args_list:
            if len(call[0]) >= 2 and call[0][1] == "create_subentry_devices":
                create_devices_call = call
                break

        assert create_devices_call is not None

    @pytest.mark.asyncio
    async def test_recalculate_service_handler(
        self, mock_hass: HomeAssistant, mock_entry_window_configs: ConfigEntry
    ) -> None:
        """Test the recalculate service handler."""
        # Mock coordinator that will be used by the service handler
        mock_coordinator = AsyncMock()
        mock_coordinator.async_refresh = AsyncMock()

        # Mock config entries
        mock_hass.config_entries.async_entries.return_value = [
            mock_entry_window_configs
        ]

        with (
            patch(
                "custom_components.solar_window_system.SolarWindowSystemCoordinator",
                return_value=mock_coordinator,
            ),
            patch("custom_components.solar_window_system._create_subentry_devices"),
            patch(
                "custom_components.solar_window_system.dr.async_get",
                return_value=Mock(),
            ),
        ):
            await self._call_async_setup_entry(mock_hass, mock_entry_window_configs)

            # Verify recalculate service was registered
            assert mock_hass.services.async_register.called
            recalculate_handler = None
            for call in mock_hass.services.async_register.call_args_list:
                if call[0][1] == "solar_window_system_recalculate":
                    recalculate_handler = call[0][2]
                    break
            assert recalculate_handler is not None

            # Test the service handler
            service_call = Mock()
            service_call.data = {}
            await recalculate_handler(service_call)

            mock_coordinator.async_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_recalculate_service_handler_with_window_id(
        self, mock_hass: HomeAssistant, mock_entry_window_configs: ConfigEntry
    ) -> None:
        """Test the recalculate service handler with specific window_id."""
        # Mock coordinator that will be used by the service handler
        mock_coordinator = AsyncMock()
        mock_coordinator.async_refresh = AsyncMock()

        # Mock config entries
        mock_hass.config_entries.async_entries.return_value = [
            mock_entry_window_configs
        ]

        with (
            patch(
                "custom_components.solar_window_system.SolarWindowSystemCoordinator",
                return_value=mock_coordinator,
            ),
            patch("custom_components.solar_window_system._create_subentry_devices"),
            patch(
                "custom_components.solar_window_system.dr.async_get",
                return_value=Mock(),
            ),
        ):
            await self._call_async_setup_entry(mock_hass, mock_entry_window_configs)

            # Get the service handler
            service_calls = mock_hass.services.async_register.call_args_list
            recalculate_handler = None
            for call in service_calls:
                if call[0][1] == "solar_window_system_recalculate":
                    recalculate_handler = call[0][2]
                    break

            # Test service call with window_id
            service_call = Mock()
            service_call.data = {"window_id": "test_window"}

            await recalculate_handler(service_call)

            mock_coordinator.async_refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_subentry_devices_service_handler(
        self, mock_hass: HomeAssistant, mock_entry_global: ConfigEntry
    ) -> None:
        """Test the create_subentry_devices service handler."""
        # Mock config entries
        mock_group_entry = Mock()
        mock_group_entry.data = {"entry_type": "group_configs"}
        mock_window_entry = Mock()
        mock_window_entry.data = {"entry_type": "window_configs"}

        mock_hass.config_entries.async_entries.return_value = [
            mock_group_entry,
            mock_window_entry,
        ]

        with (
            patch(
                "custom_components.solar_window_system._create_subentry_devices"
            ) as mock_create_devices,
            patch(
                "custom_components.solar_window_system.dr.async_get",
                return_value=Mock(),
            ),
        ):
            await self._call_async_setup_entry(mock_hass, mock_entry_global)

            # Get the service handler
            service_calls = mock_hass.services.async_register.call_args_list
            create_devices_handler = None
            for call in service_calls:
                if call[0][1] == "create_subentry_devices":
                    create_devices_handler = call[0][2]
                    break

            assert create_devices_handler is not None

            # Test service call
            service_call = Mock()

            await create_devices_handler(service_call)

            # Verify _create_subentry_devices was called for both entries
            assert mock_create_devices.call_count == 2
            mock_create_devices.assert_any_call(mock_hass, mock_group_entry)
            mock_create_devices.assert_any_call(mock_hass, mock_window_entry)

    @pytest.mark.asyncio
    async def test_create_subentry_devices_group(
        self, mock_hass: HomeAssistant
    ) -> None:
        """Test creating devices for group subentries."""
        # Mock device registry
        mock_device_registry = Mock()
        mock_device = Mock()
        mock_device.name = "Test Group"
        mock_device.id = "device_id"
        mock_device.config_entries_subentries = []
        mock_device_registry.async_get_or_create = Mock(return_value=mock_device)

        # Mock subentry
        mock_subentry = Mock()
        mock_subentry.subentry_type = "group"
        mock_subentry.title = "Test Group"

        # Mock entry
        mock_entry = Mock()
        mock_entry.entry_id = "test_entry_id"
        mock_entry.subentries = {"group_1": mock_subentry}

        with patch(
            "custom_components.solar_window_system.dr.async_get",
            return_value=mock_device_registry,
        ):
            from custom_components.solar_window_system import _create_subentry_devices

            await _create_subentry_devices(mock_hass, mock_entry)

            mock_device_registry.async_get_or_create.assert_called_once_with(
                config_entry_id="test_entry_id",
                config_subentry_id="group_1",
                identifiers={(DOMAIN, "group_group_1")},
                name="Test Group",
                manufacturer="SolarWindowSystem",
                model="GroupConfig",
            )

    @pytest.mark.asyncio
    async def test_create_subentry_devices_window(
        self, mock_hass: HomeAssistant
    ) -> None:
        """Test creating devices for window subentries."""
        # Mock device registry
        mock_device_registry = Mock()
        mock_device = Mock()
        mock_device.name = "Test Window"
        mock_device.id = "device_id"
        mock_device.config_entries_subentries = []
        mock_device_registry.async_get_or_create = Mock(return_value=mock_device)

        # Mock subentry
        mock_subentry = Mock()
        mock_subentry.subentry_type = "window"
        mock_subentry.title = "Test Window"

        # Mock entry
        mock_entry = Mock()
        mock_entry.entry_id = "test_entry_id"
        mock_entry.subentries = {"window_1": mock_subentry}

        with patch(
            "custom_components.solar_window_system.dr.async_get",
            return_value=mock_device_registry,
        ):
            from custom_components.solar_window_system import _create_subentry_devices

            await _create_subentry_devices(mock_hass, mock_entry)

            mock_device_registry.async_get_or_create.assert_called_once_with(
                config_entry_id="test_entry_id",
                config_subentry_id="window_1",
                identifiers={(DOMAIN, "window_window_1")},
                name="Test Window",
                manufacturer="SolarWindowSystem",
                model="WindowConfig",
            )

    @pytest.mark.asyncio
    async def test_create_subentry_devices_no_subentries(
        self, mock_hass: HomeAssistant
    ) -> None:
        """Test creating devices when no subentries exist."""
        # Mock entry without subentries
        mock_entry = Mock()
        mock_entry.subentries = None

        with patch("custom_components.solar_window_system.dr.async_get"):
            from custom_components.solar_window_system import _create_subentry_devices

            await _create_subentry_devices(mock_hass, mock_entry)

            # Should not fail and should not create any devices

    @pytest.mark.asyncio
    async def test_handle_config_entry_update(
        self, mock_hass: HomeAssistant, mock_entry_window_configs: ConfigEntry
    ) -> None:
        """Test config entry update handler."""
        # Mock coordinator
        mock_coordinator = Mock()
        mock_coordinator.async_reconfigure = AsyncMock()

        # Setup hass data
        mock_hass.data = {
            DOMAIN: {
                mock_entry_window_configs.entry_id: {"coordinator": mock_coordinator}
            }
        }

        with (
            patch(
                "custom_components.solar_window_system._create_subentry_devices"
            ) as mock_create_devices,
            patch.object(
                mock_hass.config_entries, "async_unload_platforms"
            ) as mock_unload,
            patch.object(
                mock_hass.config_entries, "async_forward_entry_setups"
            ) as mock_forward,
        ):
            from custom_components.solar_window_system import (
                _handle_config_entry_update,
            )

            await _handle_config_entry_update(mock_hass, mock_entry_window_configs)

            mock_create_devices.assert_called_once_with(
                mock_hass, mock_entry_window_configs
            )
            mock_coordinator.async_reconfigure.assert_called_once()
            mock_unload.assert_called_once_with(
                mock_entry_window_configs, ["select", "sensor", "binary_sensor"]
            )
            mock_forward.assert_called_once_with(
                mock_entry_window_configs, ["select", "sensor", "binary_sensor"]
            )

    @pytest.mark.asyncio
    async def test_async_unload_entry_global_config(
        self, mock_hass: HomeAssistant, mock_entry_global: ConfigEntry
    ) -> None:
        """Test unloading global config entry."""
        mock_hass.config_entries.async_unload_platforms.return_value = True

        from custom_components.solar_window_system import async_unload_entry

        result = await async_unload_entry(mock_hass, mock_entry_global)

        assert result is True
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_entry_global, ["sensor", "number", "text", "select", "switch"]
        )

    @pytest.mark.asyncio
    async def test_async_unload_entry_window_configs(
        self, mock_hass: HomeAssistant, mock_entry_window_configs: ConfigEntry
    ) -> None:
        """Test unloading window configs entry."""
        # Setup hass data
        mock_hass.data = {
            DOMAIN: {mock_entry_window_configs.entry_id: {"coordinator": Mock()}}
        }
        mock_hass.config_entries.async_unload_platforms.return_value = True

        from custom_components.solar_window_system import async_unload_entry

        result = await async_unload_entry(mock_hass, mock_entry_window_configs)

        assert result is True
        # Verify coordinator was cleaned up
        assert mock_entry_window_configs.entry_id not in mock_hass.data[DOMAIN]
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_entry_window_configs, ["select", "sensor", "binary_sensor"]
        )

    @pytest.mark.asyncio
    async def test_async_unload_entry_group_configs(
        self, mock_hass: HomeAssistant, mock_entry_group_configs: ConfigEntry
    ) -> None:
        """Test unloading group configs entry."""
        # Setup hass data
        mock_hass.data = {
            DOMAIN: {mock_entry_group_configs.entry_id: {"coordinator": Mock()}}
        }
        mock_hass.config_entries.async_unload_platforms.return_value = True

        from custom_components.solar_window_system import async_unload_entry

        result = await async_unload_entry(mock_hass, mock_entry_group_configs)

        assert result is True
        # Verify coordinator was cleaned up
        assert mock_entry_group_configs.entry_id not in mock_hass.data[DOMAIN]
        mock_hass.config_entries.async_unload_platforms.assert_called_once_with(
            mock_entry_group_configs, ["select", "sensor"]
        )

    @pytest.mark.asyncio
    async def test_service_registration_debug_calculation(
        self, mock_hass: HomeAssistant, mock_entry_global: ConfigEntry
    ) -> None:
        """Test that debug_calculation service is registered only once."""
        # Mock device registry
        mock_device_registry = Mock()
        mock_device_registry.devices = Mock()
        mock_device_registry.devices.get_entry = Mock(return_value=None)
        mock_device_registry.async_get_or_create = Mock()

        with patch(
            "custom_components.solar_window_system.dr.async_get",
            return_value=mock_device_registry,
        ):
            # First call should register the service
            await self._call_async_setup_entry(mock_hass, mock_entry_global)

            # Find the debug_calculation service registration
            debug_calculation_call = None
            for call in mock_hass.services.async_register.call_args_list:
                if (
                    len(call[0]) >= 2
                    and call[0][1] == "solar_window_system_debug_calculation"
                ):
                    debug_calculation_call = call
                    break

            assert debug_calculation_call is not None

    @pytest.mark.asyncio
    async def test_debug_calculation_service_handler_success(
        self, mock_hass: HomeAssistant
    ) -> None:
        """Test debug_calculation service handler with successful execution."""
        from custom_components.solar_window_system import (
            _handle_debug_calculation_service,
        )
        from homeassistant.core import ServiceCall

        # Mock service call
        mock_call = Mock(spec=ServiceCall)
        mock_call.data = {"window_id": "test_window", "filename": "test_debug.json"}

        # Mock config entry
        mock_config_entry = Mock()
        mock_config_entry.data = {"entry_type": "window_configs"}
        mock_config_entry.entry_id = "test_entry_id"

        # Mock coordinator
        mock_coordinator = AsyncMock()
        mock_debug_data = {
            "window_id": "test_window",
            "timestamp": "2025-08-28T10:00:00Z",
            "solar_radiation": 500.0,
            "temperatures": {"indoor": 22.0, "outdoor": 25.0},
            "calculation": {"power_total": 150.0, "shade_required": True},
        }
        mock_coordinator.create_debug_data.return_value = mock_debug_data

        # Setup mock hass
        mock_hass.config_entries.async_entries.return_value = [mock_config_entry]
        mock_hass.data = {DOMAIN: {"test_entry_id": {"coordinator": mock_coordinator}}}
        mock_hass.config.config_dir = "/tmp"

        # Mock file operations
        mock_file_handle = Mock()
        mock_file_handle.__enter__ = Mock(return_value=mock_file_handle)
        mock_file_handle.__exit__ = Mock(return_value=None)
        with (
            patch(
                "pathlib.Path.open", Mock(return_value=mock_file_handle)
            ) as mock_file,
            patch("json.dump") as mock_json_dump,
            patch.object(
                mock_hass.services, "async_call", AsyncMock()
            ) as mock_service_call,
        ):
            await _handle_debug_calculation_service(mock_hass, mock_call)

            # Verify debug data was created
            mock_coordinator.create_debug_data.assert_called_once_with("test_window")

            # Verify file was written
            mock_file.assert_called_once()
            mock_json_dump.assert_called_once_with(
                mock_debug_data,
                mock_file.return_value.__enter__.return_value,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

            # Verify notification was sent
            mock_service_call.assert_called_once_with(
                "persistent_notification",
                "create",
                {
                    "title": "Debug File Created",
                    "message": "Debug calculation file saved to: test_debug.json",
                },
            )

    @pytest.mark.asyncio
    async def test_debug_calculation_service_handler_no_window_id(
        self, mock_hass: HomeAssistant
    ) -> None:
        """Test debug_calculation service handler without window_id."""
        from custom_components.solar_window_system import (
            _handle_debug_calculation_service,
        )
        from homeassistant.core import ServiceCall

        # Mock service call without window_id
        mock_call = Mock(spec=ServiceCall)
        mock_call.data = {}

        with patch("custom_components.solar_window_system._LOGGER") as mock_logger:
            await _handle_debug_calculation_service(mock_hass, mock_call)

            # Verify error was logged
            mock_logger.error.assert_called_once_with(
                "Window ID is required for debug calculation"
            )

    @pytest.mark.asyncio
    async def test_debug_calculation_service_handler_no_debug_data(
        self, mock_hass: HomeAssistant
    ) -> None:
        """Test debug_calculation service handler when no debug data is created."""
        from custom_components.solar_window_system import (
            _handle_debug_calculation_service,
        )
        from homeassistant.core import ServiceCall

        # Mock service call
        mock_call = Mock(spec=ServiceCall)
        mock_call.data = {"window_id": "test_window"}

        # Mock config entry
        mock_config_entry = Mock()
        mock_config_entry.data = {"entry_type": "window_configs"}
        mock_config_entry.entry_id = "test_entry_id"

        # Mock coordinator that returns None
        mock_coordinator = AsyncMock()
        mock_coordinator.create_debug_data.return_value = None

        # Setup mock hass
        mock_hass.config_entries.async_entries.return_value = [mock_config_entry]
        mock_hass.data = {DOMAIN: {"test_entry_id": {"coordinator": mock_coordinator}}}

        with patch("custom_components.solar_window_system._LOGGER") as mock_logger:
            await _handle_debug_calculation_service(mock_hass, mock_call)

            # Verify error was logged
            mock_logger.error.assert_called_once_with(
                "Could not create debug data for window: %s", "test_window"
            )

    @pytest.mark.asyncio
    async def test_debug_calculation_service_handler_file_error(
        self, mock_hass: HomeAssistant
    ) -> None:
        """Test debug_calculation service handler with file write error."""
        from custom_components.solar_window_system import (
            _handle_debug_calculation_service,
        )
        from homeassistant.core import ServiceCall

        # Mock service call
        mock_call = Mock(spec=ServiceCall)
        mock_call.data = {"window_id": "test_window"}

        # Mock config entry
        mock_config_entry = Mock()
        mock_config_entry.data = {"entry_type": "window_configs"}
        mock_config_entry.entry_id = "test_entry_id"

        # Mock coordinator
        mock_coordinator = AsyncMock()
        mock_debug_data = {"test": "data"}
        mock_coordinator.create_debug_data.return_value = mock_debug_data

        # Setup mock hass
        mock_hass.config_entries.async_entries.return_value = [mock_config_entry]
        mock_hass.data = {DOMAIN: {"test_entry_id": {"coordinator": mock_coordinator}}}
        mock_hass.config.config_dir = "/tmp"

        # Mock file operations to raise OSError
        with (
            patch("pathlib.Path.open", side_effect=OSError("Permission denied")),
            patch("custom_components.solar_window_system._LOGGER") as mock_logger,
        ):
            await _handle_debug_calculation_service(mock_hass, mock_call)

            # Verify exception was logged
            mock_logger.exception.assert_called_once_with("Failed to create debug file")

    async def _call_async_setup_entry(
        self, hass: HomeAssistant, entry: ConfigEntry
    ) -> bool:
        """Call async_setup_entry with proper imports."""
        from custom_components.solar_window_system import async_setup_entry

        return await async_setup_entry(hass, entry)
