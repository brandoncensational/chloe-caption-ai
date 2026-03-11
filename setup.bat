@echo off
title Censational Social Media Manager - First Time Setup

cd /d "%~dp0"

echo.
echo  ============================================
echo   Censational Social Media Manager - Setup
echo  ============================================
echo.

:: Check Python is installed
python --version 2>nul
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not on your PATH.
    echo  Download it from: https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b
)

:: Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo  [1/3] Creating virtual environment...
    python -m venv venv
) else (
    echo  [1/3] Virtual environment already exists, skipping.
)

:: Activate it
call venv\Scripts\activate.bat

:: Install dependencies
echo  [2/3] Installing dependencies (this may take a minute)...
pip install -r requirements.txt --quiet

:: Create .env if it doesn't exist
if not exist ".env" (
    echo  [3/3] Creating .env file...
    copy .env.example .env
    echo.
    echo  ============================================
    echo   ACTION REQUIRED:
    echo   Open the .env file in this folder and
    echo   paste your Anthropic API key like this:
    echo   ANTHROPIC_API_KEY=sk-ant-xxxxxxx
    echo  ============================================
) else (
    echo  [3/3] .env file already exists, skipping.
)

echo.
echo  Setup complete! Double-click launch.bat to start the app.
echo.
pause
