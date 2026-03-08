@echo off
title Import Katie's Captions from Google Drive

cd /d "%~dp0"

echo.
echo  ============================================================
echo   Katie Riedel - Caption Import
echo   Sep / Oct / Nov 2025 + Jan / Feb 2026
echo   48 real captions from Google Drive batch files
echo  ============================================================
echo.

call venv\Scripts\activate.bat
python import_katie_captions.py

echo.
pause
