@echo off
REM Quality Gate for Solar Window System
REM Runs all quality checks before committing

setlocal enabledelayedexpansion

echo =========================================
echo   Solar Window System - Quality Gate
echo =========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo [WARNING] No virtual environment detected
    echo It is recommended to use a virtual environment to avoid
    echo conflicts with system Python packages.
    echo To set up:
    echo   scripts\setup-dev.bat
    echo Or manually:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements-test.txt
    echo.
    timeout /t 3 /nobreak >nul
)

set FAILURES=0

REM Ruff format (code formatting)
echo Running: Ruff format - code formatting
venv\Scripts\ruff.exe format --check custom_components\solar_window_system tests >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ruff format - code formatting
) else (
    echo [FAIL] Ruff format - code formatting
    echo   Run 'venv\Scripts\ruff.exe format .' to fix formatting issues
    set /a FAILURES+=1
)
echo.

REM Ruff lint
echo Running: Ruff - linting
venv\Scripts\ruff.exe check custom_components\solar_window_system tests >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ruff - linting
) else (
    echo [FAIL] Ruff - linting
    echo   Run 'venv\Scripts\ruff.exe check --fix .' to auto-fix issues
    set /a FAILURES+=1
)
echo.

REM Pyright
echo Running: Pyright - type checking
venv\Scripts\python.exe -m pyright .
if %ERRORLEVEL% EQU 0 (
    echo [OK] Pyright - type checking
) else (
    echo [FAIL] Pyright - type checking
    set /a FAILURES+=1
)
echo.

REM Pytest
echo Running: Pytest - test suite
venv\Scripts\python.exe -c "import pytest" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [SKIP] Pytest not installed in venv
    echo   Run: venv\Scripts\pip install -r requirements-test.txt
) else (
    venv\Scripts\python.exe -m pytest tests\ -q --tb=short >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Pytest - test suite
    ) else (
        echo [FAIL] Pytest - test suite
        echo   Run 'venv\Scripts\python.exe -m pytest tests\' for details
        set /a FAILURES+=1
    )
)
echo.

REM Summary
echo =========================================
echo   Quality Gate Summary
echo =========================================
if %FAILURES% EQU 0 (
    echo [OK] All checks passed!
    echo.
    echo Code is ready to commit.
    exit /b 0
) else (
    echo [FAIL] %FAILURES% checks failed
    echo.
    echo Please fix the issues above before committing.
    exit /b 1
)