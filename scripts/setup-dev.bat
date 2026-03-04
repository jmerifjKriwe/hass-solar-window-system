@echo off
REM Development Environment Setup for Solar Window System
REM Sets up a complete Python environment for HA custom component development

setlocal enabledelayedexpansion

echo =========================================
echo   Solar Window System - Dev Setup
echo =========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [31mError:[0m Python not found in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [32m✓ Python version:[0m %PYVER%
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [31mError:[0m Failed to create virtual environment
        exit /b 1
    )
    echo [32m✓ Virtual environment created[0m
) else (
    echo [32m✓ Virtual environment exists[0m
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [31mError:[0m Failed to activate virtual environment
    exit /b 1
)
echo [32m✓ Virtual environment activated[0m
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1
echo [32m✓ pip upgraded[0m
echo.

REM Install core dependencies
echo Installing core dependencies...

echo Installing pytest and plugins...
pip install pytest==8.0.0 ^
    pytest-asyncio==0.23.4 ^
    pytest-homeassistant-custom-component==0.13.104 ^
    pytest-cov==4.1.0 ^
    pytest-timeout==2.3.1 ^
    pytest-xdist==3.5.0 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [31mError:[0m Failed to install pytest
    exit /b 1
)
echo [32m  ✓ pytest (testing framework)[0m

echo Installing ruff and pyright...
pip install ruff==0.9.9 pyright==1.1.356 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [31mError:[0m Failed to install ruff/pyright
    exit /b 1
)
echo [32m  ✓ ruff (format + lint), pyright (type checking)[0m

echo Installing type stubs...
pip install types-homeassistant-stubs==2026.2.3 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [33m  ! types-homeassistant-stubs not available (optional)[0m
) else (
    echo [32m  ✓ type stubs (optional)[0m
)

echo.
echo [32m✓ Core dependencies installed[0m
echo.

REM Create requirements.txt for reproducibility
echo Creating requirements-dev.txt...
(
echo # Core testing framework
echo pytest==8.0.0
echo pytest-asyncio==0.23.4
echo pytest-homeassistant-custom-component==0.13.104
echo pytest-cov==4.1.0
echo pytest-timeout==2.3.1
echo pytest-xdist==3.5.0
echo.
echo # Code quality
echo ruff==0.9.9
echo pyright==1.1.356
echo.
echo # Type stubs ^(optional^)
echo types-homeassistant-stubs==2026.2.3
echo.
echo # Development tools
echo pre-commit==3.7.0
) > requirements-dev.txt
echo [32m✓ requirements-dev.txt created[0m
echo.

REM Install pre-commit hooks
echo Installing pre-commit hooks...
pip install pre-commit >nul 2>&1
pre-commit install >nul 2>&1
echo [32m✓ pre-commit hooks installed[0m
echo.

REM Install git commit-msg hook
echo Installing git commit-msg hook...
call scripts\install-hooks.bat
echo.

REM Run initial quality gate
echo Running initial quality gate...
echo.
call scripts\quality-gate.bat

echo.
echo =========================================
echo   Development Environment Ready!
echo =========================================
echo.
echo To activate the environment, run:
echo   venv\Scripts\activate.bat
echo.
echo To deactivate, run:
echo   deactivate
echo.
echo To run tests:
echo   pytest tests/
echo.
echo To run quality gate:
echo   scripts\quality-gate.bat
echo.
echo To format code:
echo   ruff format .
echo.
echo For Home Assistant testing:
echo   See scripts\setup-homeassistant-test.bat
echo.
