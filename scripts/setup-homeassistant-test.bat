@echo off
REM Home Assistant Test Environment Setup
REM Sets up a test environment for testing the custom component

setlocal enabledelayedexpansion

echo =========================================
echo   Home Assistant Test Environment Setup
echo =========================================
echo.

echo This script will:
echo 1. Install Home Assistant in a Python virtual environment
echo 2. Set up necessary test dependencies
echo 3. Create a test configuration
echo.
echo Note: This creates a TEST environment, not for production use!
echo.

REM Create HA-specific virtual environment
set HA_VENV=ha_test_env

if exist "%HA_VENV%" (
    echo Removing old test environment...
    rmdir /s /q "%HA_VENV%" 2>nul
)

echo Creating Home Assistant test environment...
python -m venv %HA_VENV%
if %ERRORLEVEL% NEQ 0 (
    echo [31mError:[0m Failed to create virtual environment
    exit /b 1
)
echo [32m✓ Test environment created[0m
echo.

REM Activate virtual environment
echo Activating test environment...
call %HA_VENV%\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [31mError:[0m Failed to activate virtual environment
    exit /b 1
)
echo [32m✓ Test environment activated[0m
echo.

REM Install Home Assistant with test dependencies
echo Installing Home Assistant 2026.2.3...
pip install homeassistant==2026.2.3 pytest-homeassistant-custom-component==0.13.104 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [31mError:[0m Failed to install Home Assistant
    exit /b 1
)
echo [32m✓ Home Assistant installed[0m
echo.

REM Create test configuration script
echo Creating test runner...
(
echo #!/usr/bin/env python3
echo """Test runner for Solar Window System in isolated HA environment."""
echo.
echo import os
echo import sys
echo import subprocess
echo.
echo def run_tests(^):
echo     """Run tests in the HA environment."""
echo     print("=" * 50^)
echo     print("  Solar Window System - Test Runner"^)
echo     print("=" * 50^)
echo     print(^)
echo     print("Running tests with Home Assistant integration..."^)
echo     print(^)
echo.
echo     # Run pytest
echo     result = subprocess.run(
echo         [sys.executable, "-m", "pytest",
echo          "tests/",
echo          "-v",
echo          "--tb=short",
echo          "--cov=custom_components/solar_window_system",
echo          "--cov-report=term-missing"],
echo         cwd=os.path.dirname(os.path.abspath(__file__^)^)
echo     ^)
echo.
echo     return result.returncode
echo.
echo if __name__ == "__main__":
echo     sys.exit(run_tests(^)^)
) > test_runner.py
echo [32m✓ Test runner created[0m
echo.

REM Create activation script
echo Creating activation script...
(
echo @echo off
echo REM Activate the Home Assistant test environment
echo.
echo call ha_test_env\Scripts\activate.bat
echo.
echo echo Home Assistant test environment activated
echo echo Python:
echo python --version
echo echo.
echo echo Home Assistant:
echo python -c "import homeassistant; print(homeassistant.__version__)"
echo echo.
echo echo To run tests:
echo echo   python test_runner.py
echo echo.
echo echo To deactivate:
echo echo   deactivate
) > activate_test_env.bat
echo [32m✓ Activation script created[0m
echo.

REM Create requirements file
echo Creating requirements-ha-test.txt...
(
echo # Home Assistant Test Environment
echo # Install with: pip install -r requirements-ha-test.txt
echo.
echo # Home Assistant core
echo homeassistant==2026.2.3
echo.
echo # Testing framework
echo pytest-homeassistant-custom-component==0.13.104
echo.
echo # Coverage reporting
echo pytest-cov==4.1.0
) > requirements-ha-test.txt
echo [32m✓ requirements-ha-test.txt created[0m
echo.

echo =========================================
echo   Test Environment Setup Complete!
echo =========================================
echo.
echo To use the test environment:
echo.
echo 1. Activate the environment:
echo    activate_test_env.bat
echo.
echo 2. Run tests:
echo    python test_runner.py
echo.
echo 3. Deactivate when done:
echo    deactivate
echo.
echo Note: This environment is isolated from your dev environment.
echo You can switch between dev (venv) and test (ha_test_env) as needed.
echo.
