@echo off
REM Quality Gate for Solar Window System
REM Runs all quality checks before committing

setlocal enabledelayedexpansion

echo =========================================
echo   Solar Window System - Quality Gate
echo =========================================
echo.

set FAILURES=0

REM Ruff format (code formatting)
echo Running: Ruff format - code formatting
ruff format --check custom_components\solar_window_system tests >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ruff format - code formatting
) else (
    echo [FAIL] Ruff format - code formatting
    echo   Run 'ruff format .' to fix formatting issues
    set /a FAILURES+=1
)
echo.

REM Ruff lint
echo Running: Ruff - linting
ruff check custom_components\solar_window_system tests >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ruff - linting
) else (
    echo [FAIL] Ruff - linting
    echo   Run 'ruff check --fix .' to auto-fix issues
    set /a FAILURES+=1
)
echo.

REM Pyright
echo Running: Pyright - type checking
python -m pyright custom_components\solar_window_system >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Pyright - type checking
) else (
    echo [FAIL] Pyright - type checking
    echo   Check pyright output above for details
    set /a FAILURES+=1
)
echo.

REM Pytest
echo Running: Pytest - test suite
python -m pytest tests -q --tb=no >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Pytest - test suite
) else (
    echo [FAIL] Pytest - test suite
    echo   Run 'pytest tests/ -v' for details
    set /a FAILURES+=1
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
