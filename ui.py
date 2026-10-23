"""
National University Bangladesh AI Assistant
Intelligent Network Launcher & Port Controller
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

# Base directory detection
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

if not (BASE_DIR / "main.py").exists():
    BASE_DIR = Path(os.getcwd())

DEFAULT_PORT = 5005
DEFAULT_HOST = "0.0.0.0"


def detect_lan_ip() -> str:
    """Detects primary local area network (LAN) IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not send actual traffic; simply determines routing interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        if ip and not ip.startswith("127.") and ip != "0.0.0.0":
            return ip
    except Exception:
        pass
    finally:
        s.close()

    try:
        hostname = socket.gethostname()
        for addr in socket.gethostbyname_ex(hostname)[2]:
            if not addr.startswith("127.") and not addr.startswith("169.254"):
                return addr
    except Exception:
        pass

    return "127.0.0.1"


def get_python_exe():
    """Finds the Python interpreter in virtual environment or fallback."""
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


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Checks whether a TCP port is currently open and bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, int(port))) == 0


def find_first_free_port(start_port: int = DEFAULT_PORT, max_tries: int = 50) -> int:
    """Finds the next available port starting from start_port."""
    for p in range(start_port, start_port + max_tries):
        if not is_port_in_use(p):
            return p
    return start_port


def kill_process_on_port(port: int):
    """Terminates processes listening on the given port on Windows."""
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


class NetworkLauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NU AI Assistant — Intelligent Network Launcher")
        self.root.geometry("740x650")
        self.root.minsize(660, 520)
        self.root.configure(bg="#FFFFFF")

        self.lan_ip = detect_lan_ip()
        self.current_port = DEFAULT_PORT
        self.server_proc = None
        self.is_running = False
        self.python_exe = get_python_exe()

        self.auto_fallback_var = tk.BooleanVar(value=True)

        self.setup_ui()
        self.check_initial_state()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_ui(self):
        # 1. Header Frame (Jet Black & Crimson Red Accent)
        hdr = tk.Frame(self.root, bg="#111827", padx=16, pady=12, bd=1, relief="solid")
        hdr.pack(fill="x", padx=12, pady=(12, 6))

        title_row = tk.Frame(hdr, bg="#111827")
        title_row.pack(fill="x")

        title = tk.Label(
            title_row,
            text="🎓 National University AI Assistant",
            font=("Segoe UI", 15, "bold"),
            bg="#111827",
            fg="#FFFFFF",
        )
        title.pack(side="left")

        version_badge = tk.Label(
            title_row,
            text="PRO v2.5",
            font=("Segoe UI", 8, "bold"),
            bg="#DC2626",
            fg="white",
            padx=6,
            pady=2,
        )
        version_badge.pack(side="right")

        subtitle = tk.Label(
            hdr,
            text="Intelligent Network Launcher • Multi-Device LAN Distribution • Live Port Manager",
            font=("Segoe UI", 9),
            bg="#111827",
            fg="#E5E7EB",
        )
        subtitle.pack(anchor="w", pady=(3, 0))

        # 2. Network & Port Configuration Frame (White Card with Black/Red Accents)
        cfg_frame = tk.LabelFrame(
            self.root,
            text="  🌐 Network & Port Management  ",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#DC2626",
            bd=1,
            relief="solid",
            padx=12,
            pady=8,
        )
        cfg_frame.pack(fill="x", padx=12, pady=4)

        # Row 1: LAN IP info & Port Input
        row1 = tk.Frame(cfg_frame, bg="#FFFFFF")
        row1.pack(fill="x", pady=2)

        tk.Label(
            row1,
            text="Host IP:",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#111827",
        ).pack(side="left")

        self.lbl_detected_ip = tk.Label(
            row1,
            text=f"{self.lan_ip} (LAN) / 127.0.0.1 (Local)",
            font=("Consolas", 10, "bold"),
            bg="#F9FAFB",
            fg="#DC2626",
            padx=8,
            pady=2,
            bd=1,
            relief="solid",
        )
        self.lbl_detected_ip.pack(side="left", padx=(6, 16))

        tk.Label(
            row1,
            text="Port:",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#111827",
        ).pack(side="left")

        self.port_entry = tk.Entry(
            row1,
            font=("Consolas", 10, "bold"),
            width=8,
            justify="center",
            bg="#FFFFFF",
            fg="#111827",
            insertbackground="#111827",
            bd=1,
            relief="solid",
        )
        self.port_entry.insert(0, str(self.current_port))
        self.port_entry.pack(side="left", padx=6)

        # Port control buttons
        btn_apply_port = tk.Button(
            row1,
            text="Apply Port",
            command=self.apply_port,
            font=("Segoe UI", 8, "bold"),
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
        )
        btn_apply_port.pack(side="left", padx=4)

        btn_free_port = tk.Button(
            row1,
            text="Find Free Port",
            command=self.find_and_set_free_port,
            font=("Segoe UI", 8, "bold"),
            bg="#111827",
            fg="white",
            activebackground="#374151",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=2,
        )
        btn_free_port.pack(side="left", padx=4)

        btn_reset_port = tk.Button(
            row1,
            text="Reset (5005)",
            command=self.reset_default_port,
            font=("Segoe UI", 8),
            bg="#F3F4F6",
            fg="#111827",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=6,
            pady=2,
        )
        btn_reset_port.pack(side="left", padx=4)

        # Row 2: Auto-fallback toggle & Live URLs
        row2 = tk.Frame(cfg_frame, bg="#FFFFFF")
        row2.pack(fill="x", pady=(6, 2))

        cb_fallback = tk.Checkbutton(
            row2,
            text="Auto-Fallback to next free port if occupied",
            variable=self.auto_fallback_var,
            font=("Segoe UI", 8),
            bg="#FFFFFF",
            fg="#111827",
            selectcolor="#FFFFFF",
            activebackground="#FFFFFF",
            activeforeground="#DC2626",
        )
        cb_fallback.pack(side="left")

        # 3. Status Banner (Black Bar with Red/White Status)
        self.status_frame = tk.Frame(self.root, bg="#111827", bd=1, relief="solid")
        self.status_frame.pack(fill="x", padx=12, pady=6)

        status_inner = tk.Frame(self.status_frame, bg="#111827", padx=12, pady=8)
        status_inner.pack(fill="x")

        self.lbl_status = tk.Label(
            status_inner,
            text="🔴 STATUS: STOPPED (OFFLINE)",
            font=("Segoe UI", 11, "bold"),
            bg="#111827",
            fg="#EF4444",
        )
        self.lbl_status.pack(side="left")

        self.lbl_urls = tk.Label(
            status_inner,
            text=f"Local: http://127.0.0.1:{self.current_port}  |  LAN: http://{self.lan_ip}:{self.current_port}",
            font=("Consolas", 9),
            bg="#111827",
            fg="#FFFFFF",
        )
        self.lbl_urls.pack(side="right")

        # 4. Main Action Command Bar (White Bar with Red & Black Buttons)
        action_bar = tk.Frame(self.root, bg="#FFFFFF")
        action_bar.pack(fill="x", padx=12, pady=6)

        # Big START Button (Crimson Red)
        self.btn_start = tk.Button(
            action_bar,
            text="▶  START SERVER",
            command=self.start_program,
            font=("Segoe UI", 11, "bold"),
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=7,
            bd=0,
        )
        self.btn_start.pack(side="left", padx=(0, 8))

        # Big STOP Button (Jet Black)
        self.btn_stop = tk.Button(
            action_bar,
            text="⏹  STOP",
            command=self.stop_program,
            font=("Segoe UI", 11, "bold"),
            bg="#111827",
            fg="white",
            activebackground="#000000",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=7,
            bd=0,
            state="disabled",
        )
        self.btn_stop.pack(side="left", padx=(0, 8))

        # RESTART Button (Crimson Red)
        self.btn_restart = tk.Button(
            action_bar,
            text="🔄 RESTART",
            command=self.restart_program,
            font=("Segoe UI", 9, "bold"),
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=7,
            bd=0,
        )
        self.btn_restart.pack(side="left", padx=(0, 8))

        # Open Local Chat (Jet Black)
        self.btn_open_local = tk.Button(
            action_bar,
            text="🌐 Local Chat",
            command=self.open_local_browser,
            font=("Segoe UI", 9, "bold"),
            bg="#111827",
            fg="white",
            activebackground="#374151",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=7,
            bd=0,
        )
        self.btn_open_local.pack(side="left", padx=(0, 6))

        # Open LAN Chat (Crimson Red)
        self.btn_open_lan = tk.Button(
            action_bar,
            text="📱 LAN Chat",
            command=self.open_lan_browser,
            font=("Segoe UI", 9, "bold"),
            bg="#DC2626",
            fg="white",
            activebackground="#B91C1C",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=7,
            bd=0,
        )
        self.btn_open_lan.pack(side="left", padx=(0, 6))

        # Staff Portal (Jet Black)
        self.btn_admin = tk.Button(
            action_bar,
            text="🔒 Staff Portal",
            command=self.open_admin,
            font=("Segoe UI", 9, "bold"),
            bg="#111827",
            fg="white",
            activebackground="#374151",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=7,
            bd=0,
        )
        self.btn_admin.pack(side="left", padx=(0, 6))

        # Copy URLs button (White with Black border)
        btn_copy = tk.Button(
            action_bar,
            text="📋 Copy Link",
            command=self.copy_lan_url,
            font=("Segoe UI", 8, "bold"),
            bg="#FFFFFF",
            fg="#111827",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=8,
            pady=6,
        )
        btn_copy.pack(side="left")

        # 5. Terminal Logs Header & Body
        log_header = tk.Frame(self.root, bg="#FFFFFF")
        log_header.pack(fill="x", padx=12, pady=(8, 4))

        tk.Label(
            log_header,
            text="Live Service & Terminal Logs:",
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg="#111827",
        ).pack(side="left")

        tk.Button(
            log_header,
            text="Clear",
            command=self.clear_logs,
            font=("Segoe UI", 8, "bold"),
            bg="#DC2626",
            fg="#FFFFFF",
            relief="flat",
            cursor="hand2",
            padx=8,
            pady=1,
        ).pack(side="right")

        self.log_text = scrolledtext.ScrolledText(
            self.root,
            wrap="word",
            bg="#111827",
            fg="#FFFFFF",
            insertbackground="#DC2626",
            font=("Consolas", 9),
            bd=1,
            relief="solid",
        )
        self.log_text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log("Intelligent Network Launcher initialized.")
        self.log(f"Project Base: {BASE_DIR}")
        self.log(f"Detected LAN IPv4: {self.lan_ip}")
        self.log(f"Default Server Port: {self.current_port}")
        self.log(f"Python Runtime: {self.python_exe}")

    def log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")

    def clear_logs(self):
        self.log_text.delete("1.0", "end")

    def update_url_labels(self):
        self.lbl_urls.config(
            text=f"Local: http://127.0.0.1:{self.current_port}  |  LAN: http://{self.lan_ip}:{self.current_port}"
        )

    def apply_port(self):
        if self.is_running:
            messagebox.showwarning("Server Running", "Please stop the server before switching ports.")
            return

        raw = self.port_entry.get().strip()
        try:
            val = int(raw)
            if not (1024 <= val <= 65535):
                raise ValueError("Port must be between 1024 and 65535.")
        except Exception as e:
            messagebox.showerror("Invalid Port", f"Invalid port number: {e}")
            return

        self.current_port = val
        self.update_url_labels()
        self.log(f"Configured port set to {self.current_port}")
        if is_port_in_use(self.current_port):
            self.log(f"⚠️ Warning: Port {self.current_port} is currently IN USE by another process.")
        else:
            self.log(f"✓ Port {self.current_port} is verified free.")

    def find_and_set_free_port(self):
        free_p = find_first_free_port(start_port=self.current_port)
        self.current_port = free_p
        self.port_entry.delete(0, "end")
        self.port_entry.insert(0, str(free_p))
        self.update_url_labels()
        self.log(f"✓ Found free port: {free_p}")

    def reset_default_port(self):
        self.current_port = DEFAULT_PORT
        self.port_entry.delete(0, "end")
        self.port_entry.insert(0, str(DEFAULT_PORT))
        self.update_url_labels()
        self.log(f"Reset port to default: {DEFAULT_PORT}")

    def check_initial_state(self):
        if is_port_in_use(self.current_port):
            self.set_running_state(True)
            self.log(f"Detected service already active on port {self.current_port}.")
        else:
            self.set_running_state(False)

    def set_running_state(self, running: bool):
        self.is_running = running
        if running:
            self.lbl_status.config(text=f"🔴 STATUS: ONLINE (Port {self.current_port})", fg="#FFFFFF")
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
            self.btn_restart.config(state="normal")
            self.port_entry.config(state="disabled")
        else:
            self.lbl_status.config(text="🔴 STATUS: STOPPED (OFFLINE)", fg="#ef4444")
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            self.btn_restart.config(state="disabled")
            self.port_entry.config(state="normal")

    def start_program(self):
        target_port = self.current_port
        try:
            target_port = int(self.port_entry.get().strip())
            self.current_port = target_port
        except Exception:
            pass

        if is_port_in_use(target_port):
            if self.auto_fallback_var.get():
                free_port = find_first_free_port(target_port + 1)
                self.log(f"⚠️ Port {target_port} is busy. Auto-falling back to port {free_port}...")
                self.current_port = free_port
                self.port_entry.delete(0, "end")
                self.port_entry.insert(0, str(free_port))
                self.update_url_labels()
                target_port = free_port
            else:
                if messagebox.askyesno(
                    "Port Busy",
                    f"Port {target_port} is already in use.\nTerminate the occupying process and restart?",
                ):
                    kill_process_on_port(target_port)
                    time.sleep(1)
                else:
                    return

        self.log(f"Starting NU AI Assistant on 0.0.0.0:{target_port}...")
        self.lbl_status.config(text="⏳ STATUS: STARTING...", fg="#FCA5A5")

        main_py = BASE_DIR / "main.py"
        if not main_py.exists():
            messagebox.showerror("Error", f"Could not find main.py at:\n{main_py}")
            self.set_running_state(False)
            return

        cmd = [self.python_exe, str(main_py), "--host", DEFAULT_HOST, "--port", str(target_port)]
        try:
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            env = os.environ.copy()
            env["PORT"] = str(target_port)
            env["HOST"] = DEFAULT_HOST

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

            threading.Thread(target=self._stream_logs, daemon=True).start()
            threading.Thread(target=self._monitor_startup, args=(target_port,), daemon=True).start()

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

    def _monitor_startup(self, port: int):
        for _ in range(90):
            time.sleep(0.5)
            if self.server_proc and self.server_proc.poll() is not None:
                self.root.after(0, lambda: self.set_running_state(False))
                self.root.after(0, lambda: self.log("⚠️ Server process exited unexpectedly. Please check logs above."))
                return
            if is_port_in_use(port):
                self.root.after(0, lambda: self.set_running_state(True))
                self.root.after(0, lambda: self.log("✓ Server is ONLINE and accepting connections!"))
                self.root.after(0, lambda: self.log(f"  • Local: http://127.0.0.1:{port}"))
                self.root.after(0, lambda: self.log(f"  • LAN (Mobile/Devices): http://{self.lan_ip}:{port}"))
                return
        self.root.after(0, lambda: self.log("⚠️ Startup timeout. Please inspect logs above."))

    def stop_program(self):
        self.log(f"Stopping server on port {self.current_port}...")
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

        kill_process_on_port(self.current_port)
        self.set_running_state(False)
        self.log(f"✓ Server stopped. Port {self.current_port} released.")

    def restart_program(self):
        self.log("Restarting server...")
        self.stop_program()
        time.sleep(1)
        self.start_program()

    def open_local_browser(self):
        url = f"http://127.0.0.1:{self.current_port}"
        self.log(f"Opening browser (Local): {url}")
        webbrowser.open(url)

    def open_lan_browser(self):
        url = f"http://{self.lan_ip}:{self.current_port}"
        self.log(f"Opening browser (LAN): {url}")
        webbrowser.open(url)

    def open_admin(self):
        url = f"http://127.0.0.1:{self.current_port}/admin"
        self.log(f"Opening Staff Portal: {url}")
        webbrowser.open(url)

    def copy_lan_url(self):
        url = f"http://{self.lan_ip}:{self.current_port}"
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.log(f"✓ Copied LAN URL to clipboard: {url}")
        messagebox.showinfo("Copied", f"LAN URL copied to clipboard:\n{url}")

    def on_close(self):
        if self.is_running:
            if messagebox.askyesno("Exit Confirmation", "The server is running. Stop server before closing?"):
                self.stop_program()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = NetworkLauncherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
