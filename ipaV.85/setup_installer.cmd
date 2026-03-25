@echo off
setlocal

echo ============================================
echo  VERA Dependency Installer
echo ============================================
echo.

:: Find Python — try common install locations in order
set PYTHON=
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%ProgramFiles%\Python314\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%P
        goto :found_python
    )
)

:: Last resort — check PATH
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    set PYTHON=python
    goto :found_python
)

echo ERROR: Python 3.11 or newer not found.
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
pause
exit /b 1

:found_python
echo Found Python: %PYTHON%
echo.

echo Installing VERA dependencies...
%PYTHON% -m pip install --upgrade pip
%PYTHON% -m pip install sounddevice faster-whisper pynput pystray pillow customtkinter pyttsx3 pycaw kokoro-onnx soundfile
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Downloading and installing espeak-ng (required for Kokoro TTS)...
curl -L -o "%TEMP%\espeak-ng.msi" "https://github.com/espeak-ng/espeak-ng/releases/download/1.52.0/espeak-ng.msi"
msiexec /i "%TEMP%\espeak-ng.msi" /quiet /norestart
echo espeak-ng installed.

echo.
echo Downloading Kokoro voice model files (one-time, ~310MB)...
if not exist "%~dp0data\models" mkdir "%~dp0data\models"
curl -L -o "%~dp0data\models\kokoro-v1.0.onnx" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
curl -L -o "%~dp0data\models\voices-v1.0.bin" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
echo Model files downloaded.

echo.
echo ============================================
echo  Setup complete! You can now launch VERA.
echo ============================================
pause
