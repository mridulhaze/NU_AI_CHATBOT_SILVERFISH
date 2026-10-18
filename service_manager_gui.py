"""
National University Bangladesh AI Assistant & Support Platform
Desktop GUI Service Manager (Start, Stop, Monitor & Browser Launcher)
"""

import os
import sys
import time
import socket
import shutil
import signal
import subprocess
import threading
import webbrowser
import multiprocessing
from pathlib import Path

# MUST be first for Windows PyInstaller binaries
if __name__ == "__main__":
    multiprocessing.freeze_support()

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Determine Base Directory safely whether frozen or raw python
if getattr(sys, 'frozen', False):
    # Running as compiled .exe
    EXE_DIR = Path(sys.executable).resolve().parent
    BASE_DIR = EXE_DIR if (EXE_DIR / "main.py").exists() else Path(__file__).resolve().parent
else:
    # Running as script
    BASE_DIR = Path(__file__).resolve().parent

if not (BASE_DIR / "main.py").exists():
    BASE_DIR = Path(os.getcwd())

# Try loading .env if exists
env_path = BASE_DIR / ".env"
if env_path.exists():
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

DEFAULT_PORT = int(os.getenv("PORT", "8000"))
DEFAULT_HOST = os.getenv("HOST", "127.0.0.1")

def find_available_port(start_port=8000, max_attempts=50):
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            if s.connect_ex((DEFAULT_HOST, p)) != 0:
                return p
    return start_port

def get_python_exe():
    """
    Finds the real Python interpreter executable.
    When running as a PyInstaller frozen .exe, sys.executable points to NU_AI_Server_Manager.exe.
    Using sys.executable to spawn main.py would mistakenly re-launch the GUI!
    """
    # 1. Check local virtual environment inside BASE_DIR
    venv_py = BASE_DIR / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)

    venv_py_unix = BASE_DIR / ".venv" / "bin" / "python"
    if venv_py_unix.exists():
        return str(venv_py_unix)

    if not getattr(sys, 'frozen', False):
        return sys.executable

    # Check candidates
    candidates = [
        shutil.which("python"),
        shutil.which("python.exe"),
        shutil.which("pythonw"),
        shutil.which("py"),
        r"C:\Users\RAKIB\AppData\Local\Programs\Python\Python313\python.exe",
        r"C:\Program Files\Python313\python.exe",
        r"C:\Program Files\Python312\python.exe",
        r"C:\Program Files\Python311\python.exe",
        r"C:\Python313\python.exe",
        r"C:\Python312\python.exe",
    ]
    for cand in candidates:
        if cand and os.path.exists(cand):
            return cand
    return "python"

class ServerManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("National University AI Platform — Service Controller")
        self.root.geometry("820x640")
        self.root.minsize(700, 520)
        
        # App State
        self.server_process = None
        self.log_reader_thread = None
        self.is_running = False
        self.start_time = None
        self.python_bin = get_python_exe()

        self.apply_theme()
        self.create_widgets()
        self.check_initial_port_status()
        
        # Handle Window Close Event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def apply_theme(self):
        # Configure Colors
        self.c_bg = "#0f172a"          # Slate 900
        self.c_card = "#1e293b"        # Slate 800
        self.c_card_border = "#334155" # Slate 700
        self.c_emerald = "#059669"     # Emerald 600
        self.c_emerald_dark = "#065f46"
        self.c_red = "#dc2626"         # Red 600
        self.c_blue = "#2563eb"        # Blue 600
        self.c_amber = "#d97706"       # Amber 600
        self.c_text = "#f8fafc"        # Slate 50
        self.c_text_muted = "#94a3b8"  # Slate 400
        self.c_terminal_bg = "#020617" # Slate 950

        self.root.configure(bg=self.c_bg)

    def create_widgets(self):
        # --- Top Header Frame ---
        hdr_frame = tk.Frame(self.root, bg=self.c_card, bd=0, relief="flat")
        hdr_frame.pack(fill="x", padx=14, pady=(12, 8))

        hdr_inner = tk.Frame(hdr_frame, bg=self.c_card)
        hdr_inner.pack(fill="x", padx=16, pady=12)

        # Title and Subtitle
        title_box = tk.Frame(hdr_inner, bg=self.c_card)
        title_box.pack(side="left")

        lbl_title = tk.Label(
            title_box, 
            text="🏛️ National University Bangladesh", 
            font=("Segoe UI", 15, "bold"), 
            bg=self.c_card, 
            fg=self.c_emerald
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            title_box, 
            text="AI Academic Assistant, Support Token Service & 24/7 Knowledge Engine", 
            font=("Segoe UI", 9), 
            bg=self.c_card, 
            fg=self.c_text_muted
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Port Selector on Right
        port_box = tk.Frame(hdr_inner, bg=self.c_card)
        port_box.pack(side="right", padx=4)

        lbl_port = tk.Label(port_box, text="Port:", font=("Segoe UI", 9, "bold"), bg=self.c_card, fg=self.c_text)
        lbl_port.pack(side="left", padx=(0, 4))

        # Check if default port is free, otherwise select next available
        init_port = DEFAULT_PORT
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.3)
            if s.connect_ex((DEFAULT_HOST, init_port)) == 0:
                try:
                    import urllib.request
                    req = urllib.request.Request(f"http://{DEFAULT_HOST}:{init_port}/api/health", headers={"User-Agent": "NU-Server-Manager"})
                    with urllib.request.urlopen(req, timeout=0.6) as resp:
                        pass
                except Exception:
                    init_port = find_available_port(8000)

        self.port_var = tk.StringVar(value=str(init_port))
        self.ent_port = tk.Entry(port_box, textvariable=self.port_var, width=6, font=("Segoe UI", 9, "bold"), justify="center")
        self.ent_port.pack(side="left")

        # --- Status Banner Frame ---
        self.status_frame = tk.Frame(self.root, bg=self.c_card, bd=1, relief="solid", highlightbackground=self.c_card_border)
        self.status_frame.pack(fill="x", padx=14, pady=(0, 8))

        status_inner = tk.Frame(self.status_frame, bg=self.c_card)
        status_inner.pack(fill="x", padx=16, pady=10)

        self.lbl_status_icon = tk.Label(status_inner, text="🔴", font=("Segoe UI", 16), bg=self.c_card)
        self.lbl_status_icon.pack(side="left", padx=(0, 8))

        status_text_box = tk.Frame(status_inner, bg=self.c_card)
        status_text_box.pack(side="left")

        self.lbl_status_text = tk.Label(
            status_text_box, 
            text="SERVICE STATUS: STOPPED (Offline)", 
            font=("Segoe UI", 11, "bold"), 
            bg=self.c_card, 
            fg="#f87171"
        )
        self.lbl_status_text.pack(anchor="w")

        self.lbl_url_text = tk.Label(
            status_text_box, 
            text=f"Service URL: http://{DEFAULT_HOST}:{self.port_var.get()} (Click 'Start Service' to launch)", 
            font=("Segoe UI", 9), 
            bg=self.c_card, 
            fg=self.c_text_muted
        )
        self.lbl_url_text.pack(anchor="w", pady=(1, 0))

        self.lbl_uptime = tk.Label(
            status_inner, 
            text="Uptime: 00:00:00", 
            font=("Segoe UI", 9, "bold"), 
            bg=self.c_card, 
            fg=self.c_text_muted
        )
        self.lbl_uptime.pack(side="right")

        # --- Control Action Buttons Frame ---
        btn_frame = tk.Frame(self.root, bg=self.c_bg)
        btn_frame.pack(fill="x", padx=14, pady=4)

        self.btn_start = tk.Button(
            btn_frame, 
            text="▶ Start Service", 
            command=self.start_service, 
            font=("Segoe UI", 10, "bold"), 
            bg=self.c_emerald, 
            fg="white", 
            activebackground=self.c_emerald_dark, 
            activeforeground="white",
            relief="flat", 
            cursor="hand2", 
            padx=14, 
            pady=6
        )
        self.btn_start.pack(side="left", padx=(0, 6))

        self.btn_stop = tk.Button(
            btn_frame, 
            text="⏹ Stop Service", 
            command=self.stop_service, 
            font=("Segoe UI", 10, "bold"), 
            bg=self.c_red, 
            fg="white", 
            activebackground="#b91c1c", 
            activeforeground="white",
            relief="flat", 
            cursor="hand2", 
            padx=14, 
            pady=6,
            state="disabled"
        )
        self.btn_stop.pack(side="left", padx=(0, 6))

        self.btn_restart = tk.Button(
            btn_frame, 
            text="🔄 Restart", 
            command=self.restart_service, 
            font=("Segoe UI", 10, "bold"), 
            bg="#334155", 
            fg="white", 
            relief="flat", 
            cursor="hand2", 
            padx=10, 
            pady=6
        )
        self.btn_restart.pack(side="left", padx=(0, 6))

        self.btn_browser = tk.Button(
            btn_frame, 
            text="🌐 Open Web Assistant", 
            command=self.open_browser, 
            font=("Segoe UI", 10, "bold"), 
            bg=self.c_blue, 
            fg="white", 
            relief="flat", 
            cursor="hand2", 
            padx=10, 
            pady=6
        )
        self.btn_browser.pack(side="left", padx=(0, 6))

        self.btn_proposal = tk.Button(
            btn_frame, 
            text="📑 Open Proposal (DOCX)", 
            command=self.open_proposal, 
            font=("Segoe UI", 9, "bold"), 
            bg=self.c_amber, 
            fg="white", 
            relief="flat", 
            cursor="hand2", 
            padx=10, 
            pady=6
        )
        self.btn_proposal.pack(side="right")

        # --- Terminal Log Viewer ---
        log_label_frame = tk.Frame(self.root, bg=self.c_bg)
        log_label_frame.pack(fill="x", padx=14, pady=(10, 2))

        lbl_log_title = tk.Label(
            log_label_frame, 
            text="🖥️ Live Server & 24/7 Agent Terminal Logs:", 
            font=("Segoe UI", 10, "bold"), 
            bg=self.c_bg, 
            fg=self.c_text
        )
        lbl_log_title.pack(side="left")

        btn_clear = tk.Button(
            log_label_frame, 
            text="🧹 Clear Logs", 
            command=self.clear_logs, 
            font=("Segoe UI", 8, "bold"), 
            bg=self.c_card, 
            fg=self.c_text_muted, 
            relief="flat", 
            cursor="hand2",
            padx=6,
            pady=1
        )
        btn_clear.pack(side="right")

        self.txt_logs = scrolledtext.ScrolledText(
            self.root, 
            wrap="word", 
            bg=self.c_terminal_bg, 
            fg="#4ade80", 
            insertbackground="white", 
            font=("Consolas", 9), 
            bd=1, 
            relief="solid", 
            highlightbackground=self.c_card_border
        )
        self.txt_logs.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.log("National University AI Platform Service Controller initialized.")
        self.log(f"Working Directory: {BASE_DIR}")
        self.log(f"Detected Python Runtime: {self.python_bin}")

    def log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        self.txt_logs.insert("end", f"[{timestamp}] {text}\n")
        self.txt_logs.see("end")

    def clear_logs(self):
        self.txt_logs.delete("1.0", "end")

    def check_port_in_use(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((DEFAULT_HOST, port)) == 0

    def is_ai_service_running(self, port: int) -> bool:
        try:
            import urllib.request
            req = urllib.request.Request(f"http://{DEFAULT_HOST}:{port}/api/health", headers={"User-Agent": "NU-Server-Manager"})
            with urllib.request.urlopen(req, timeout=0.8) as resp:
                return resp.status == 200
        except Exception:
            return False

    def check_initial_port_status(self):
        try:
            port = int(self.port_var.get().strip())
            if self.check_port_in_use(port):
                if self.is_ai_service_running(port):
                    self.set_ui_running(port)
                    self.log(f"Detected active National University AI service on port {port}.")
                else:
                    self.log(f"⚠️ Port {port} is occupied by another application.")
                    free_port = find_available_port(8000)
                    self.port_var.set(str(free_port))
                    self.lbl_url_text.config(text=f"Service URL: http://{DEFAULT_HOST}:{free_port} (Click 'Start Service' to launch)")
                    self.log(f"Auto-selected available port: {free_port}")
        except Exception:
            pass

    def set_ui_running(self, port):
        self.is_running = True
        self.lbl_status_icon.config(text="🟢")
        self.lbl_status_text.config(text=f"SERVICE STATUS: RUNNING (Port {port})", fg="#4ade80")
        self.lbl_url_text.config(text=f"Service URL: http://{DEFAULT_HOST}:{port} • Ready for students & solvers")
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        if not self.start_time:
            self.start_time = time.time()
        self.update_uptime()

    def set_ui_stopped(self):
        self.is_running = False
        self.start_time = None
        self.lbl_status_icon.config(text="🔴")
        self.lbl_status_text.config(text="SERVICE STATUS: STOPPED (Offline)", fg="#f87171")
        self.lbl_url_text.config(text=f"Service URL: http://{DEFAULT_HOST}:{self.port_var.get()} (Offline)")
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.lbl_uptime.config(text="Uptime: 00:00:00")

    def update_uptime(self):
        if self.is_running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours, rem = divmod(elapsed, 3600)
            minutes, seconds = divmod(rem, 60)
            self.lbl_uptime.config(text=f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            self.root.after(1000, self.update_uptime)

    def start_service(self):
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Port", "Please enter a valid numeric port number (e.g. 8000).")
            return

        if self.check_port_in_use(port):
            if messagebox.askyesno("Port Busy", f"Port {port} is already in use.\nDo you want to terminate the existing process and restart?"):
                self.kill_process_on_port(port)
                time.sleep(1)
            else:
                return

        self.log(f"Starting National University AI Platform on port {port}...")
        self.lbl_status_icon.config(text="🟡")
        self.lbl_status_text.config(text="SERVICE STATUS: STARTING...", fg="#facc15")

        # Explicitly invoke Python interpreter to run main.py (NEVER sys.executable inside PyInstaller)
        python_exe = get_python_exe()
        main_script = BASE_DIR / "main.py"

        if not main_script.exists():
            messagebox.showerror("Missing main.py", f"Could not find main.py at:\n{main_script}")
            self.set_ui_stopped()
            return

        cmd = [python_exe, str(main_script), "--port", str(port)]
        
        try:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            proc_env = os.environ.copy()
            proc_env["PORT"] = str(port)
            proc_env["HOST"] = DEFAULT_HOST

            self.server_process = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creation_flags,
                env=proc_env
            )

            # Start background thread to capture stdout/stderr logs
            self.log_reader_thread = threading.Thread(target=self.read_server_logs, daemon=True)
            self.log_reader_thread.start()

            # Wait briefly and verify startup
            threading.Thread(target=self.wait_for_startup, args=(port,), daemon=True).start()

        except Exception as e:
            self.log(f"Error launching server: {e}")
            messagebox.showerror("Launch Error", f"Failed to start server:\n{e}")
            self.set_ui_stopped()

    def wait_for_startup(self, port):
        for _ in range(25):
            time.sleep(0.5)
            if self.check_port_in_use(port):
                self.root.after(0, lambda: self.set_ui_running(port))
                self.root.after(0, lambda: self.log("✓ Server is active, healthy, and accepting requests!"))
                return
        self.root.after(0, lambda: self.log("⚠️ Server startup timed out. Check output logs above."))

    def read_server_logs(self):
        if not self.server_process:
            return
        try:
            for line in iter(self.server_process.stdout.readline, ""):
                if line:
                    clean_line = line.strip()
                    self.root.after(0, lambda l=clean_line: self.log(l))
        except Exception:
            pass

    def stop_service(self):
        self.log("Stopping National University AI Platform service...")
        port = int(self.port_var.get().strip()) if self.port_var.get().strip().isdigit() else DEFAULT_PORT

        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=2)
            except Exception:
                try:
                    self.server_process.kill()
                except Exception:
                    pass
            self.server_process = None

        self.kill_process_on_port(port)
        self.set_ui_stopped()
        self.log("✓ Service successfully stopped and port released.")

    def kill_process_on_port(self, port: int):
        if sys.platform == "win32":
            try:
                output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True, text=True)
                pids = set()
                for line in output.strip().splitlines():
                    parts = line.split()
                    if len(parts) >= 5 and "LISTENING" in line:
                        pids.add(parts[-1])
                for pid in pids:
                    if pid and pid != "0":
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
                        self.log(f"Terminated process PID {pid} on port {port}.")
            except Exception:
                pass

    def restart_service(self):
        self.stop_service()
        time.sleep(1)
        self.start_service()

    def open_browser(self):
        port = self.port_var.get().strip()
        url = f"http://{DEFAULT_HOST}:{port}"
        self.log(f"Opening default browser at: {url}")
        webbrowser.open(url)

    def open_proposal(self):
        docx_path = BASE_DIR / "project_proposal" / "project_proposal.docx"
        pdf_path = BASE_DIR / "project_proposal" / "project_proposal.pdf"
        target = docx_path if docx_path.exists() else pdf_path
        if target.exists():
            self.log(f"Opening Proposal Document: {target.name}")
            os.startfile(str(target))
        else:
            messagebox.showwarning("File Not Found", f"Proposal document not found at:\n{target}")

    def on_close(self):
        if self.is_running:
            if messagebox.askyesno("Exit Controller", "The AI Platform service is currently running.\nDo you want to stop the service and exit?"):
                self.stop_service()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = ServerManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
