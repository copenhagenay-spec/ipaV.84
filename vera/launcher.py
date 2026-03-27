"""VERA launcher — finds pythonw.exe and runs assistant.py with no console window."""
import os
import sys
import shutil
import subprocess

if getattr(sys, 'frozen', False):
    base = os.path.dirname(sys.executable)
else:
    base = os.path.dirname(os.path.abspath(__file__))

pythonw = shutil.which("pythonw") or shutil.which("python")
assistant = os.path.join(base, "assistant.py")
subprocess.Popen([pythonw, assistant], cwd=base)
