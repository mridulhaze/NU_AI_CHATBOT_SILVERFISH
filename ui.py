"""
National University Bangladesh AI Assistant
Simple Controller GUI (START / STOP / BROWSER)
"""

import os
import sys
import time
import socket
import subprocess
import threading
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

# Base directory
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

if not (BASE_DIR / "main.py").exists():
    BASE_DIR = Path(os.getcwd())

PORT = 8000
HOST = "127.0.0.1"


def get_python_exe():
    """Finds the virtual environment Python interpreter."""
    candidates = [
        BASE_DIR / ".venv" / "Scripts" / "python.exe",
        BASE_DIR / "venv" / "Scripts" / "python.exe",
        BASE_DIR / ".venv" / "bin" / "python",
        BASE_DIR / "venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.exists():
            return str(c)

    if not getattr(sys, "frozen", False):
        return sys.executable

    return "python"


def is_port_in_use(port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((HOST, port)) == 0


def kill_port(port=PORT):
    if sys.platform == "win32":
        try:
            output = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True, text=True)
            pids = set()
            for line in output.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and "LISTENING" in line:
                    pids.add(parts[-1])
            for pid in pids:
                if pid and pid != "0":
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, capture_output=True)
        except Exception:
            pass


class SimpleServiceUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NU AI Assistant — Simple Controller")
        self.root.geometry("680x520")
        self.root.minsize(580, 440)
        self.root.configure(bg="#0f172a")

        self.server_proc = None
        self.is_running = False
        self.python_exe = get_python_exe()

        self.setup_ui()
        self.check_initial_state()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # 1. Header Frame
        hdr = tk.Frame(self.root, bg="#1e293b", padx=16, pady=12)
        hdr.pack(fill="x", padx=12, pady=(12, 6))

        title = tk.Label(
            hdr,
            text="🎓 National University AI Chatbot",
            font=("Segoe UI", 14, "bold"),
            bg="#1e293b",
            fg="#10b981",
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            hdr,
            text="One-Click Service Controller (Start, Stop & Launch Browser)",
            font=("Segoe UI", 9),
            bg="#1e293b",
            fg="#94a3b8",
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # 2. Status Banner
        self.status_frame = tk.Frame(self.root, bg="#1e293b", bd=1, relief="solid")
        self.status_frame.pack(fill="x", padx=12, pady=6)

        status_inner = tk.Frame(self.status_frame, bg="#1e293b", padx=14, pady=10)
        status_inner.pack(fill="x")

        self.lbl_status = tk.Label(
            status_inner,
            text="🔴 STATUS: STOPPED (OFFLINE)",
            font=("Segoe UI", 12, "bold"),
            bg="#1e293b",
            fg="#ef4444",
        )
        self.lbl_status.pack(side="left")

        self.lbl_url = tk.Label(
            status_inner,
            text=f"http://{HOST}:{PORT}",
            font=("Segoe UI", 10, "bold"),
            bg="#1e293b",
            fg="#60a5fa",
        )
        self.lbl_url.pack(side="right")

        # 3. Main Action Buttons (START / STOP / BROWSER)
        btn_bar = tk.Frame(self.root, bg="#0f172a")
        btn_bar.pack(fill="x", padx=12, pady=8)

        # Big START Button
        self.btn_start = tk.Button(
            btn_bar,
            text="▶  START",
            command=self.start_program,
            font=("Segoe UI", 12, "bold"),
            bg="#059669",
            fg="white",
            activebackground="#047857",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            bd=0,
        )
        self.btn_start.pack(side="left", padx=(0, 10))

        # Big STOP Button
        self.btn_stop = tk.Button(
            btn_bar,
            text="⏹  STOP",
            command=self.stop_program,
            font=("Segoe UI", 12, "bold"),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            bd=0,
            state="disabled",
        )
        self.btn_stop.pack(side="left", padx=(0, 10))

        # Open Web App Button
        self.btn_open = tk.Button(
            btn_bar,
            text="🌐 Open Web App",
            command=self.open_browser,
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            bd=0,
        )
        self.btn_open.pack(side="left", padx=(0, 8))

        # Open Staff Portal Button
        self.btn_admin = tk.Button(
            btn_bar,
            text="🔒 Staff Portal",
            command=self.open_admin,
            font=("Segoe UI", 10, "bold"),
            bg="#475569",
            fg="white",
            activebackground="#334155",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            bd=0,
        )
        self.btn_admin.pack(side="left")

        # 4. Terminal Log Output
        log_header = tk.Frame(self.root, bg="#0f172a")
        log_header.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(
            log_header,
            text="Terminal & Server Logs:",
            font=("Segoe UI", 9, "bold"),
            bg="#0f172a",
            fg="#94a3b8",
        ).pack(side="left")

        tk.Button(
            log_header,
            text="Clear Logs",
            command=self.clear_logs,
            font=("Segoe UI", 8),
            bg="#1e293b",
            fg="#cbd5e1",
            relief="flat",
            cursor="hand2",
            padx=6,
            pady=1,
        ).pack(side="right")

        self.log_text = scrolledtext.ScrolledText(
            self.root,
            wrap="word",
            bg="#020617",
            fg="#4ade80",
            insertbackground="white",
            font=("Consolas", 9),
            bd=1,
            relief="solid",
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log("Controller UI initialized.")
        self.log(f"Project Base: {BASE_DIR}")
        self.log(f"Python: {self.python_exe}")

    def log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")

    def clear_logs(self):
        self.log_text.delete("1.0", "end")

    def check_initial_state(self):
        if is_port_in_use(PORT):
            self.set_running_state(True)
            self.log(f"Detected service already active on port {PORT}.")
        else:
            self.set_running_state(False)

    def set_running_state(self, running):
        self.is_running = running
        if running:
            self.lbl_status.config(text="🟢 STATUS: RUNNING (ONLINE)", fg="#10b981")
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
        else:
            self.lbl_status.config(text="🔴 STATUS: STOPPED (OFFLINE)", fg="#ef4444")
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")

    def start_program(self):
        if is_port_in_use(PORT):
            if messagebox.askyesno("Port Busy", f"Port {PORT} is already in use.\nTerminate existing process and restart?"):
                kill_port(PORT)
                time.sleep(1)
            else:
                return

        self.log(f"Starting National University AI Program on port {PORT}...")
        self.lbl_status.config(text="🟡 STATUS: STARTING...", fg="#facc15")

        main_py = BASE_DIR / "main.py"
        if not main_py.exists():
            messagebox.showerror("Error", f"Could not find main.py at:\n{main_py}")
            self.set_running_state(False)
            return

        cmd = [self.python_exe, str(main_py), "--port", str(PORT)]
        try:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            env = os.environ.copy()
            env["PORT"] = str(PORT)
            env["HOST"] = HOST

            self.server_proc = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creation_flags,
                env=env,
            )

            # Log reader thread
            threading.Thread(target=self._stream_logs, daemon=True).start()

            # Startup monitor thread
            threading.Thread(target=self._monitor_startup, daemon=True).start()

        except Exception as e:
            self.log(f"Error starting process: {e}")
            messagebox.showerror("Launch Error", str(e))
            self.set_running_state(False)

    def _stream_logs(self):
        if not self.server_proc:
            return
        try:
            for line in iter(self.server_proc.stdout.readline, ""):
                if line:
                    clean = line.strip()
                    self.root.after(0, lambda l=clean: self.log(l))
        except Exception:
            pass

    def _monitor_startup(self):
        for _ in range(25):
            time.sleep(0.5)
            if is_port_in_use(PORT):
                self.root.after(0, lambda: self.set_running_state(True))
                self.root.after(0, lambda: self.log("✓ Server is online and ready!"))
                return
        self.root.after(0, lambda: self.log("⚠️ Startup timeout. Check logs above."))

    def stop_program(self):
        self.log("Stopping server program...")
        if self.server_proc:
            try:
                self.server_proc.terminate()
                self.server_proc.wait(timeout=2)
            except Exception:
                try:
                    self.server_proc.kill()
                except Exception:
                    pass
            self.server_proc = None

        kill_port(PORT)
        self.set_running_state(False)
        self.log("✓ Program stopped and port 8000 released.")

    def open_browser(self):
        url = f"http://{HOST}:{PORT}"
        self.log(f"Opening browser at: {url}")
        webbrowser.open(url)

    def open_admin(self):
        url = f"http://{HOST}:{PORT}/admin"
        self.log(f"Opening staff portal at: {url}")
        webbrowser.open(url)

    def on_close(self):
        if self.is_running:
            if messagebox.askyesno("Exit", "The program is running. Stop server before closing?"):
                self.stop_program()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = SimpleServiceUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
