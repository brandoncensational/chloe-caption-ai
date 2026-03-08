@echo off
title Set Up Google Drive Access

cd /d "%~dp0"

echo.
echo  ============================================================
echo   Google Drive Setup for Image Selection
echo  ============================================================
echo.
echo  Before running this, you need a Google Cloud credentials file.
echo  Steps (one-time only):
echo.
echo  1. Go to: https://console.cloud.google.com/
echo  2. Create a project (or use existing)
echo  3. Enable the Google Drive API
echo  4. Go to APIs and Services ^> Credentials
echo  5. Create OAuth 2.0 Client ID ^> Desktop App
echo  6. Download the JSON file
echo  7. Rename it to: drive_credentials.json
echo  8. Place it in the 'data' folder inside chloe_ai
echo.
echo  Then come back and press any key to continue...
echo.
pause

call venv\Scripts\activate.bat

echo.
echo  Testing Drive connection and completing OAuth...
echo.

python -c "
import sys, os
sys.path.insert(0, '.')
try:
    from drive_helper import get_drive_service, is_drive_configured
    if not is_drive_configured():
        print('ERROR: data/drive_credentials.json not found.')
        print('Please follow the steps above and re-run this script.')
        sys.exit(1)
    print('Credentials found! Opening browser for Google sign-in...')
    svc = get_drive_service()
    print('')
    print('SUCCESS! Google Drive is connected.')
    print('You can now use Drive image selection in the batch generator.')
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
"

echo.
pause
