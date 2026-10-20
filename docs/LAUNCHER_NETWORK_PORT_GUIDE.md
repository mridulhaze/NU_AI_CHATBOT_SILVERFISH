# Intelligent Network Launcher & Port Controller Guide
**National University Bangladesh AI Assistant**

## 1. Executive Summary
The Intelligent Network Launcher (`ui.py` / `UI.exe`) provides a desktop control surface for managing, monitoring, and distributing the National University AI Assistant across local workstations and multi-device campus/office Local Area Networks (LAN).

---

## 2. Network IP Detection Architecture
The launcher dynamically discovers the host machine's primary LAN IPv4 address (e.g., `192.168.0.113`) rather than binding exclusively to loopback (`127.0.0.1`) or advertising unusable wildcard addresses (`0.0.0.0`).

### 2.1 Detection Algorithm
```python
def detect_lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Determines actual routing interface without sending network traffic
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        if ip and not ip.startswith("127.") and ip != "0.0.0.0":
            return ip
    except Exception:
        pass
    finally:
        s.close()
    return "127.0.0.1"
```

### 2.2 Host Binding & Network Distribution
When the server starts:
- Subprocess arguments: `python main.py --host 0.0.0.0 --port <PORT>`
- Environment variables injected: `HOST=0.0.0.0`, `PORT=<PORT>`
- **Local Access URL:** `http://127.0.0.1:<PORT>`
- **LAN Access URL:** `http://<LAN_IP>:<PORT>` (accessible by mobile phones, tablets, and faculty laptops connected to the same Wi-Fi/Ethernet).

---

## 3. Port Management Features

| Feature | Control / Action | Behavior |
| :--- | :--- | :--- |
| **Default Port** | `5005` | Fresh configurations default to port `5005` (migrated from legacy `8000`). |
| **Port Input Entry** | Direct text field | Allows custom port configuration (1024 - 65535). |
| **Apply Port** | `[Apply Port]` button | Validates port number and updates configured target port. |
| **Find Free Port** | `[Find Free Port]` button | Probes successive TCP sockets to find the next available port. |
| **Reset Default** | `[Reset (5005)]` button | Instantly resets configured port back to default `5005`. |
| **Auto-Fallback** | Checkbox toggle | If port `5005` is occupied, automatically finds and binds the next open port without failing. |
| **Process Cleanup** | Automatic Windows kill | Can terminate orphaned zombie python processes on port collision. |

---

## 4. aristocractic Navy & Emerald UI Theme

The GUI utilizes an aristocratic executive palette:
- **Base Canvas:** Deep Navy (`#0b1120`)
- **Card Panels:** Slate Surface (`#1e293b`) with border (`#334155`)
- **Action Accents:** Emerald Green (`#059669` / `#10b981`), Cyan (`#0891b2`), Crimson (`#dc2626`)
- **Typography:** Crisp Segoe UI and monospace Consolas log terminal.

---

## 5. Compiling UI.exe with PyInstaller
The launcher is compiled into a standalone, single-file Windows executable:
```powershell
pyinstaller --noconsole --onefile --clean --name UI ui.py
```
Output binary: `D:\projects\AI_CHAT_BOT\UI.exe`
