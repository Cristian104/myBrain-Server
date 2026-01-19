# 🧠 My Brain Portal - Documentation

## System Overview
This is a custom Python web application acting as a login portal for `mybrain.world`.
It runs as a background service on the server and is exposed to the internet via Nginx and Cloudflare.

**Flow:**
`User` -> `Cloudflare Tunnel` -> `Nginx (Proxy)` -> `Python Flask App (Port 5000)`

---

## 📂 File Locations

| Component | Path | Description |
| :--- | :--- | :--- |
| **App Folder** | `/home/jorg/mybrain-portal/` | Main project folder |
| **Logic** | `~/mybrain-portal/app.py` | Python code (passwords, login logic) |
| **Login Page** | `~/mybrain-portal/templates/login.html` | HTML for the login screen |
| **Dashboard** | `~/mybrain-portal/templates/dashboard.html` | HTML for the main menu |
| **Images** | `~/mybrain-portal/static/` | Logo and other assets |
| **Service File** | `/etc/systemd/system/mybrain.service` | Auto-start configuration |
| **Nginx Config** | `/etc/nginx/sites-available/default` | Web server proxy settings |

---

## 🛠️ Management Cheat Sheet

### 1. Check Status
See if the app is running or crashed.
```bash
sudo systemctl status mybrain
