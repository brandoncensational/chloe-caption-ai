@echo off
title Censational Social Media Manager

:: ── Change this path to wherever you saved the censational folder ──────────────
set PROJECT_DIR=%~dp0

:: Move into the project folder
cd /d "%PROJECT_DIR%"

:: Activate the virtual environment
call "%PROJECT_DIR%venv\Scripts\activate.bat"

:: Check if streamlit is installed, install deps if not
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo [Setup] Installing dependencies for the first time...
    pip install -r requirements.txt
)

:: Launch the app
echo.
echo  🚀  Starting Censational Social Media Manager...
echo  🚀  Open your browser to: http://localhost:8501
echo  🚀  Press Ctrl+C in this window to stop the app.
echo.

streamlit run app.py --server.headless false

pause
