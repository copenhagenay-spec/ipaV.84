@echo off
setlocal
cd /d "%~dp0"

echo === VERA Uninstaller ===
echo This will remove VERA user data from this folder.
echo.

set /p REMOVE_ALL="Remove model, settings, and logs? (y/N): "
if /i "%REMOVE_ALL%"=="y" (
  rmdir /s /q data
  echo Removed data folder.
) else (
  echo Keeping data folder.
)

echo.
echo VERA application files remain in this folder.
echo To fully remove, delete the ipa folder manually.
pause