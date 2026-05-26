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
        _dev_mode = False
    else:
        base = os.path.dirname(exe_dir)
        _dev_mode = True  # running from launcher_out, packages are in system Python
else:
    base = os.path.dirname(os.path.abspath(__file__))
    _dev_mode = False

def _find_pythonw():
    # Prefer bundled embedded Python — skip in dev mode (python\ has no packages)
    if not _dev_mode:
        embedded = os.path.join(base, "python", "pythonw.exe")
        if os.path.exists(embedded):
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
