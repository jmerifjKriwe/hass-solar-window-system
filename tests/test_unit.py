"""Unit tests for internal functions."""
import yaml
from unittest.mock import MagicMock

from custom_components.solar_window_system import _load_config_from_files
from .mocks import MOCK_CONFIG


def test_load_config_from_files_with_mock_hass(tmp_path):
    """Test that _load_config_from_files correctly loads YAML files."""
    config_dir = tmp_path / "solar_windows"
    config_dir.mkdir()

    with open(config_dir / "windows.yaml", "w") as f:
        yaml.dump({"windows": MOCK_CONFIG["windows"]}, f)

    with open(config_dir / "groups.yaml", "w") as f:
        yaml.dump({"groups": MOCK_CONFIG["groups"]}, f)

    mock_hass = MagicMock()
    mock_hass.config.path.return_value = str(config_dir)

    result = _load_config_from_files(mock_hass)

    assert isinstance(result, dict)
    assert "groups" in result
    assert "windows" in result
    assert "test_window_south" in result["windows"]
    assert "group_with_override" in result["groups"]
    mock_hass.config.path.assert_called_once_with("solar_windows")


def test_load_config_from_files_no_files(tmp_path):
    """Test that the function returns empty dicts when no config files are present."""
    config_dir = tmp_path / "solar_windows"
    config_dir.mkdir()

    mock_hass = MagicMock()
    mock_hass.config.path.return_value = str(config_dir)

    result = _load_config_from_files(mock_hass)

    assert result == {"groups": {}, "windows": {}}


def test_load_config_from_files_empty_files(tmp_path):
    """Test that the function returns empty dicts when the YAML files are empty."""
    config_dir = tmp_path / "solar_windows"
    config_dir.mkdir()

    with open(config_dir / "windows.yaml", "w") as f:
        f.write("")

    with open(config_dir / "groups.yaml", "w") as f:
        f.write("")

    mock_hass = MagicMock()
    mock_hass.config.path.return_value = str(config_dir)

    result = _load_config_from_files(mock_hass)

    assert result == {"groups": {}, "windows": {}}
