@echo off
title Chloe's Caption AI - Database Patch

cd /d "%~dp0"

echo.
echo  ============================================
echo   Chloe's Caption AI - Database Patch
echo  ============================================
echo.

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Run the patch
echo  Applying database patch...
python database_patch.py

echo.
echo  All done! You can close this window and run launch.bat
echo.
pause
