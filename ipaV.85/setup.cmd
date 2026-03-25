@echo off
echo Installing VERA dependencies...
"%LOCALAPPDATA%\Programs\Python\Python314\python.exe" -m pip install sounddevice faster-whisper pynput pystray pillow customtkinter pyttsx3 pycaw kokoro-onnx soundfile

echo.
echo Downloading and installing espeak-ng (required for Kokoro TTS)...
curl -L -o "%TEMP%\espeak-ng.msi" "https://github.com/espeak-ng/espeak-ng/releases/download/1.52.0/espeak-ng.msi"
msiexec /i "%TEMP%\espeak-ng.msi" /quiet /norestart
echo espeak-ng installed.

echo.
echo Downloading Kokoro model files (one-time, ~310MB)...
if not exist "%~dp0data\models" mkdir "%~dp0data\models"
curl -L -o "%~dp0data\models\kokoro-v1.0.onnx" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
curl -L -o "%~dp0data\models\voices-v1.0.bin" "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
echo Model files downloaded.

echo.
echo Done! You can now run run_ipa.cmd to start VERA.
pause
