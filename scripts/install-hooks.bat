@echo off
REM Install git hooks from .git-hooks directory

setlocal enabledelayedexpansion

echo Installing git hooks...

REM Create .git/hooks directory if it doesn't exist
if not exist ".git\hooks" mkdir .git\hooks

REM Copy hooks
copy /Y .git-hooks\commit-msg .git\hooks\commit-msg >nul

echo [OK] Git hooks installed
echo.
echo Installed hooks:
echo   - commit-msg: Validates Conventional Commits format
echo.
echo See COMMIT_CONVENTIONS.md for details.
