#!/usr/bin/env python3
"""
WinRepair Toolkit GUI
- Looks for scripts in ../scripts
- Makes a temp copy of .bat files removing 'pause' lines before running so the GUI doesn't hang
- Streams output to the GUI and writes logs under logs/
- Uses cmd /c to run batch files so the system executes them correctly
"""
import subprocess
import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
from pathlib import Path
import sys
import tempfile
import shutil
import datetime

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def prepare_batch_for_gui(bat_path: Path) -> str:
    """
    Create a temporary copy of the batch file with 'pause' lines removed.
    Return the temporary path as a string (Windows path).
    """
    with open(bat_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    cleaned = []
    for line in lines:
        stripped = line.strip().lower()
        # remove standalone 'pause' and "pause>" variants
        if stripped == "pause" or stripped.startswith("pause "):
            continue
        # also remove 'pause' if appended after & or &&
        # simple heuristic: drop lines that equal pause ignoring whitespace
        cleaned.append(line)
    # ensure script exits with code
    cleaned.append("\nexit /b %ERRORLEVEL%\n")
    fd, tmp = tempfile.mkstemp(suffix=".bat", text=True)
    with open(fd, "w", encoding="utf-8", errors="ignore") as f:
        f.writelines(cleaned)
    return tmp

def run_script(cmd, update_fn, done_fn=None, log_name=None):
    """
    Run external command (list form) and stream output to update_fn.
    Optionally write to log file named log_name (under logs/).
    Runs in a daemon thread.
    """
    def target():
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        logfile = None
        if log_name:
            logfile_path = LOGS_DIR / f"{log_name}-{timestamp}.log"
            logfile = open(logfile_path, "w", encoding="utf-8", errors="ignore")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                shell=False,
            )
            for line in proc.stdout:
                update_fn(line)
                if logfile:
                    logfile.write(line)
            proc.wait()
            if done_fn:
                done_fn(proc.returncode)
        except Exception as e:
            update_fn(f"ERROR: {e}\n")
            if done_fn:
                done_fn(-1)
        finally:
            if logfile:
                logfile.close()
            # cleanup: if cmd referenced a temp batch, remove it
            try:
                # if cmd is ["cmd", "/c", "<path>"]
                if len(cmd) >= 3 and cmd[0].lower().endswith("cmd.exe") and cmd[1] == "/c":
                    tmp_candidate = Path(cmd[2])
                    if tmp_candidate.exists() and tmp_candidate.suffix.lower() == ".bat" and str(tmp_candidate).startswith(tempfile.gettempdir()):
                        try:
                            tmp_candidate.unlink()
                        except Exception:
                            pass
            except Exception:
                pass

    threading.Thread(target=target, daemon=True).start()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WinRepair Toolkit")
        self.geometry("900x540")
        self.text = ScrolledText(self, wrap=tk.WORD, height=24)
        self.text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0,8))
        tk.Button(btn_frame, text="Run Cleaner", command=self.on_cleaner).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Network Fix", command=self.on_netfix).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Open logs folder", command=self.open_logs).pack(side=tk.RIGHT, padx=6)
        if not is_admin():
            messagebox.showwarning("Administrator required", "This tool performs system operations and should be run as Administrator. Right-click the EXE and choose 'Run as administrator' to ensure operations succeed.")

    def append(self, s):
        self.text.insert(tk.END, s)
        self.text.see(tk.END)

    def on_cleaner(self):
        self.append("Starting Cleaner...\n")
        bat = SCRIPTS_DIR / "Cleaner.bat"
        if not bat.exists():
            self.append(f"{bat} not found\n")
            return
        tmp = prepare_batch_for_gui(bat)
        cmd = [str(Path(sys.executable).parent / "cmd.exe")] if False else ["cmd", "/c", tmp]
        # Note: using cmd /c <tempfile> ensures the batch runs and exits
        run_script(cmd, lambda s: self.append(s), lambda rc: self.append(f"\nCleaner finished (rc={rc})\n"), log_name="cleaner")

    def on_netfix(self):
        self.append("Starting Network Fix...\n")
        bat = SCRIPTS_DIR / "Network Fix.bat"
        if bat.exists():
            tmp = prepare_batch_for_gui(bat)
            cmd = ["cmd", "/c", tmp]
        else:
            # fallback: build a short command list for network reset
            powershell_cmd = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
                "ipconfig /release; ipconfig /renew; ipconfig /flushdns; netsh winsock reset; netsh int ip reset"
            ]
            cmd = powershell_cmd
        run_script(cmd, lambda s: self.append(s), lambda rc: self.append(f"\nNetwork Fix finished (rc={rc})\n"), log_name="netfix")

    def open_logs(self):
        LOGS_DIR.mkdir(exist_ok=True)
        try:
            subprocess.Popen(["explorer", str(LOGS_DIR)])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open logs folder: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
