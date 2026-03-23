@echo off
echo Installing VERA dependencies...
"%LOCALAPPDATA%\Programs\Python\Python314\python.exe" -m pip install sounddevice vosk pynput pystray pillow customtkinter pyttsx3 pycaw edge-tts playsound==1.2.2
echo.
echo Done! You can now run run_ipa.vbs to start VERA.
pause
