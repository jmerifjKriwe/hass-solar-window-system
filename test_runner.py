#!/usr/bin/env python3
"""Simple test runner to bypass pytest plugin issues."""

import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tests"))

# Import and run tests
if __name__ == "__main__":
    # Import the test module
    # Run each test function
    import pytest

    from tests import test_sensor

    # Run with minimal plugins
    sys.exit(
        pytest.main(
            [
                "tests/test_sensor.py",
                "-v",
                "-p",
                "no:langsmith",
                "-p",
                "no:cacheprovider",
            ]
        )
    )
