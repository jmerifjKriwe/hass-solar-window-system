from pytest_homeassistant_custom_component.common import MockConfigEntry


def test_mockentry_import():
    assert MockConfigEntry is not None
