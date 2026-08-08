# WinRepair Toolkit

Small Windows GUI wrapper around maintenance scripts.

What this repo contains
- src/gui.py â€” Tkinter GUI wrapper that runs scripts in `scripts/` and logs output.
- scripts/ â€” your batch scripts (Cleaner.bat, Network Fix.bat).
- build/build.ps1 â€” local PS helper to produce a single-file EXE using PyInstaller.
- .github/workflows/windows-build.yml â€” CI build that produces dist/WinRepairTool.exe.

Quick local run (for development)
1. Install Python 3.8+ (Windows).
2. (Optional) Create and activate a venv:
   python -m venv venv
   .\\venv\\Scripts\\activate
3. Install dependencies:
   pip install pyinstaller
4. Run the GUI directly:
   python src\\gui.py

Build a single-file EXE locally
- From repo root:
  powershell -ExecutionPolicy Bypass -File build\\build.ps1

Notes and important safety items
- Run the final EXE as Administrator (right-click -> Run as administrator) because operations like deleting C:\\Windows\\Temp and resetting network settings require elevated privileges.
- The GUI makes a temporary copy of your .bat scripts and removes `pause` lines for GUI execution; your original scripts in scripts/ are not modified.
- Signing: to avoid Windows/AV warnings, sign the EXE with a code-signing certificate before distribution.
- Antivirus: single-file EXEs packaged by PyInstaller can trigger heuristics; test widely.

License
- Add a LICENSE file you prefer (MIT recommended for open-source).
