@echo off
REM Development Environment Setup for Solar Window System
REM Sets up a complete Python environment for HA custom component development

REM Enable ANSI colors for Windows 10+
for /f "tokens=*" %%a in ('powershell -Command "$host.UI.RawUI.BackgroundColor" 2^>nul') do set "term_bg=%%a"
if not defined term_bg (
    powershell -Command "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8" 2>nul
)

setlocal enabledelayedexpansion

echo =========================================
echo   Solar Window System - Dev Setup
echo =========================================
echo.

REM Check Python 3.14
echo Checking Python version...
py -3.14 --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3.14 not found
    echo Please install Python 3.14 from https://www.python.org/
    exit /b 1
)

for /f "tokens=2" %%i in ('py -3.14 --version 2^>^&1') do set PYVER=%%i
echo [OK] Python version: %PYVER%
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    py -3.14 -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create virtual environment
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment exists
    echo [INFO] If you encounter issues, delete the venv folder and re-run this script
)
echo.

REM Verify venv was created correctly
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment is missing python.exe
    echo Please delete the venv folder and re-run this script
    exit /b 1
)

REM Install sitecustomize.py to mock Unix-only modules on Windows
echo Installing Windows compatibility shim...
(
    echo """Site customization for Windows - mock Unix-only modules."""
    echo import sys
    echo from unittest.mock import MagicMock
    echo.
    echo for mod in ["fcntl", "grp", "pwd", "termios", "tty", "resource"]:
    echo     if mod not in sys.modules:
    echo         sys.modules[mod] = MagicMock^(^)
) > venv\Lib\site-packages\sitecustomize.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create sitecustomize.py
    exit /b 1
)
echo [OK] Windows compatibility shim installed
echo.

REM Upgrade pip using venv python directly
echo Upgrading pip...
venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to upgrade pip
    exit /b 1
)
echo [OK] pip upgraded
echo.

REM Install core dependencies using venv pip directly
echo Installing core dependencies...
echo Installing dependencies from requirements-test.txt...
venv\Scripts\pip.exe install -r requirements-test.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies from requirements-test.txt
    exit /b 1
)
echo [OK] Dependencies installed
echo.
echo [OK] Core dependencies installed
echo.

REM Install pre-commit hooks using venv pip directly
echo Installing pre-commit hooks...
venv\Scripts\pip.exe install pre-commit >nul 2>&1
venv\Scripts\pre-commit.exe install >nul 2>&1
echo [OK] pre-commit hooks installed
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