"""SH|RA launcher — finds pythonw.exe and runs assistant.py with no console window."""
import os
import sys
import shutil
import subprocess

if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
    # SHRA.exe lives in launcher_out\ — assistant.py is one level up
    if os.path.exists(os.path.join(exe_dir, 'assistant.py')):
        base = exe_dir
    else:
        base = os.path.dirname(exe_dir)
else:
    base = os.path.dirname(os.path.abspath(__file__))

def _embedded_has_packages():
    """True if the embedded Python has SH|RA's dependencies installed."""
    return os.path.exists(os.path.join(base, "python", "Lib", "site-packages", "pynput"))

def _find_pythonw():
    embedded = os.path.join(base, "python", "pythonw.exe")
    if os.path.exists(embedded) and _embedded_has_packages():
        return embedded

    local = os.environ.get("LOCALAPPDATA", "")
    pf    = os.environ.get("ProgramFiles", "")
    candidates = [
        os.path.join(local, r"Programs\Python\Python314\pythonw.exe"),
        os.path.join(local, r"Programs\Python\Python313\pythonw.exe"),
        os.path.join(local, r"Programs\Python\Python312\pythonw.exe"),
        os.path.join(local, r"Programs\Python\Python311\pythonw.exe"),
        os.path.join(pf,    r"Python314\pythonw.exe"),
        os.path.join(pf,    r"Python313\pythonw.exe"),
        os.path.join(pf,    r"Python312\pythonw.exe"),
        os.path.join(pf,    r"Python311\pythonw.exe"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return shutil.which("pythonw") or shutil.which("python")

pythonw   = _find_pythonw()
assistant = os.path.join(base, "assistant.py")
env = os.environ.copy()
env["PYTHONPATH"] = base
subprocess.Popen([pythonw, assistant], cwd=base, env=env)
