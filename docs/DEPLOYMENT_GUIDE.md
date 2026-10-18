# NU_AI_CHAT_BOT — Production Deployment & Operations Guide

This guide provides end-to-end instructions for deploying the **National University Bangladesh AI Assistant** (`NU_AI_CHAT_BOT`) in a production server environment (Ubuntu Linux / Debian or Windows Server).

---

## 1. System Requirements

- **Operating System:** Ubuntu 22.04+ LTS / Debian 12 (recommended) or Windows Server 2019+
- **CPU:** 4 vCPUs minimum (8 vCPUs recommended for 1,000+ concurrent users)
- **RAM:** 8 GB minimum (16 GB recommended for in-memory ChromaDB vector cache)
- **Disk:** 50 GB SSD (for SQLite WAL files and ChromaDB indices)
- **Python Version:** Python 3.11+
- **Reverse Proxy:** Nginx 1.20+ with SSL/TLS

---

## 2. Environment Setup

### 2.1 Clone and Prepare Virtual Environment
```bash
git clone https://github.com/nu-bd/nu-ai-assistant.git /opt/nu_assistant
cd /opt/nu_assistant

# Create virtual environment with Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate

# Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.2 Configure Production Environment Variables (`.env`)
Create `/opt/nu_assistant/.env` with the following production values:
```ini
# Server Binding
HOST=127.0.0.1
PORT=8000
RELOAD=false
ENVIRONMENT=production

# Security & Rate Limiting
RATE_LIMIT_PER_MINUTE=120
ADMIN_SECRET_KEY=your_super_secure_random_admin_key_here

# AI Model Configuration
GEMINI_API_KEY=your_official_google_gemini_api_key
PRIMARY_MODEL=gemini-2.5-flash
FALLBACK_MODELS=gemini-2.0-flash,gemini-1.5-flash

# Knowledge Crawler Schedule (Minutes)
CRAWL_INTERVAL_MINUTES=30
AUTO_CRAWL_ON_STARTUP=true

# Database Paths
SQLITE_DB_PATH=data/nu_assistant.db
TOKEN_DB_PATH=data/nu_tokens.db
CHROMA_PERSIST_DIR=data/chroma_db
```

---

## 3. Database Initialization & Verification

Run the verification test suite to ensure all schemas, WAL mode, and RBAC rules are initialized:
```bash
source .venv/bin/activate
python tests/test_token_service_domain.py
python tests/test_notice_filter_service.py
```
Expected output: `OK (Ran 27 tests)`.

---

## 4. Process Management with Systemd

Create the systemd service file `/etc/systemd/system/nu-assistant.service`:
```ini
[Unit]
Description=National University Bangladesh AI Assistant Service
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/nu_assistant
EnvironmentFile=/opt/nu_assistant/.env
ExecStart=/opt/nu_assistant/.venv/bin/gunicorn backend.app:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --backlog 2048 \
    --timeout 60 \
    --keep-alive 5 \
    --access-logfile /var/log/nu-assistant/access.log \
    --error-logfile /var/log/nu-assistant/error.log

Restart=always
RestartSec=5
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo mkdir -p /var/log/nu-assistant
sudo chown -R www-data:www-data /var/log/nu-assistant /opt/nu_assistant/data
sudo systemctl daemon-reload
sudo systemctl enable nu-assistant
sudo systemctl start nu-assistant
sudo systemctl status nu-assistant
```

---

## 5. Nginx Reverse Proxy Configuration

Configure Nginx to front the application with SSL, WebSocket/SSE streaming support, and gzip compression:

`/etc/nginx/sites-available/nu-assistant.conf`:
```nginx
upstream nu_backend {
    server 127.0.0.1:8000;
    keepalive 64;
}

server {
    listen 80;
    server_name ai.nu.ac.bd;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ai.nu.ac.bd;

    ssl_certificate /etc/letsencrypt/live/ai.nu.ac.bd/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai.nu.ac.bd/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    # Static Assets Cache
    location /static/ {
        alias /opt/nu_assistant/static/;
        expires 7d;
        add_header Cache-Control "public, no-transform";
    }

    # Public Chat & Widget
    location / {
        proxy_pass http://nu_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE Streaming settings
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 120s;
    }
}
```

Enable site and reload Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/nu-assistant.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. Embeddable Widget Integration

To embed the floating assistant on any official university portal (e.g. `app11.nu.edu.bd` or `nu.ac.bd`), insert the script before `</body>`:
```html
<script 
  src="https://ai.nu.ac.bd/static/nu-chat-widget.js" 
  data-api-host="https://ai.nu.ac.bd"
  data-bot-title="NU AI Academic Assistant"
  defer>
</script>
```

---

## 7. Monitoring, Backup & Health Checks

1. **Health Check Endpoint:**
   ```bash
   curl -s http://127.0.0.1:8000/api/v1/health | jq .
   ```
2. **One-Click Maintenance Sync:**
   To re-crawl notices and optimize database indices without restarting:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/admin/sync-and-maintain \
        -H "Authorization: Bearer <ADMIN_KEY>"
   ```
3. **Automated Nightly Backup (Cron):**
   ```bash
   # Add to crontab (runs at 02:00 AM daily)
   0 2 * * * /opt/nu_assistant/.venv/bin/python -c "from token_service.service import get_token_service; get_token_service().create_system_backup()" >> /var/log/nu-assistant/backup.log 2>&1
   ```
