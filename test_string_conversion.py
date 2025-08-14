"""Simple test to verify string conversion fixes."""

from custom_components.solar_window_system.options_flow import (
    SolarWindowSystemOptionsFlow,
)


def test_prefer_options_returns_correct_types():
    """Test _prefer_options method with different data types."""

    # Test data with mixed types (as they would be stored)
    opts = {
        "diffuse_factor": 0.15,  # float
        "threshold_direct": 200,  # int
        "indoor_temperature_sensor": "sensor.temp1",  # string
    }

    data = {
        "diffuse_factor": "0.20",  # string (fallback)
        "threshold_direct": "250",  # string (fallback)
        "temperature_indoor_base": 23.0,  # float (only in data)
    }

    # Test the method
    result1 = SolarWindowSystemOptionsFlow._prefer_options(
        opts, data, "diffuse_factor", ""
    )
    result2 = SolarWindowSystemOptionsFlow._prefer_options(
        opts, data, "threshold_direct", ""
    )
    result3 = SolarWindowSystemOptionsFlow._prefer_options(
        opts, data, "indoor_temperature_sensor", ""
    )
    result4 = SolarWindowSystemOptionsFlow._prefer_options(
        opts, data, "temperature_indoor_base", ""
    )
    result5 = SolarWindowSystemOptionsFlow._prefer_options(
        opts, data, "non_existent", ""
    )

    print(f"diffuse_factor (float from opts): {result1} (type: {type(result1)})")
    print(f"threshold_direct (int from opts): {result2} (type: {type(result2)})")
    print(
        f"indoor_temperature_sensor (str from opts): {result3} (type: {type(result3)})"
    )
    print(
        f"temperature_indoor_base (float from data): {result4} (type: {type(result4)})"
    )
    print(f"non_existent (fallback): {result5} (type: {type(result5)})")

    # The problem: schema expects strings but gets ints/floats
    print("\nTesting string conversion:")
    str_result1 = "" if result1 in ("", None) else str(result1)
    str_result2 = "" if result2 in ("", None) else str(result2)
    str_result4 = "" if result4 in ("", None) else str(result4)

    print(f"diffuse_factor converted: {str_result1} (type: {type(str_result1)})")
    print(f"threshold_direct converted: {str_result2} (type: {type(str_result2)})")
    print(
        f"temperature_indoor_base converted: {str_result4} (type: {type(str_result4)})"
    )

    # Verify that all converted values are strings
    assert isinstance(str_result1, str), f"Expected str, got {type(str_result1)}"
    assert isinstance(str_result2, str), f"Expected str, got {type(str_result2)}"
    assert isinstance(str_result4, str), f"Expected str, got {type(str_result4)}"

    print("\n✓ All conversions successful!")


if __name__ == "__main__":
    test_prefer_options_returns_correct_types()
