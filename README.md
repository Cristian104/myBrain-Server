Markdown

# 🧠 My Brain Portal - Documentation

## System Overview

This is a custom Python web application acting as a dashboard and login portal for `mybrain.world`.
It runs as a Docker container on the server and is exposed to the internet via Nginx and Cloudflare.

**Flow:**
`User` -> `Cloudflare Tunnel` -> `Nginx (Proxy)` -> `Docker Container (Port 5000)` -> `Python Flask App`

---

## 📂 File Locations

| Component         | Path                         | Description                     |
| :---------------- | :--------------------------- | :------------------------------ |
| **Project Root**  | `/home/jorg/mybrain-portal/` | Main repository folder          |
| **Database**      | `instance/db.sqlite`         | SQLite database (Tasks & Users) |
| **Python App**    | `app/`                       | Source code (Routes, Models)    |
| **Templates**     | `app/templates/`             | HTML files (Dashboard, Login)   |
| **Static Assets** | `app/static/`                | CSS, JS, and Images             |
| **Docker Config** | `docker-compose.yml`         | Container definitions           |

---

## 🚀 Deployment Workflow (QA to Production)

We use a **Git-based workflow**. Never edit files directly on the server (except `.env`).

### 1. Work Locally (VS Code)

1.  Create a branch for your new feature:
    ```powershell
    git checkout -b feature/my-cool-feature
    ```
2.  Make changes, test, and commit:
    ```powershell
    git add .
    git commit -m "Added cool feature"
    git push origin feature/my-cool-feature
    ```
3.  **Merge** the branch into `main` (via GitHub PR or Terminal).

### 2. Deploy to Server (SSH)

Connect to the server and pull the `main` branch.

```bash
ssh jorg@172.22.198.147
cd ~/mybrain-portal

# 1. Get latest code
git checkout main
git pull origin main

# 2. Rebuild Container (Required if Python/HTML changed)
docker compose up -d --build
🐳 Docker Cheat Sheet
Check if it's running:

Bash

docker compose ps
View Logs (Real-time):

Bash

docker compose logs -f
Restart the App (Quick):

Bash

docker compose restart
Full Reset (Fixes most "Stuck" errors): ⚠️ This destroys the container and rebuilds it. Data in volumes (DB) is safe.

Bash

docker compose down
docker compose up -d --build

### How to update it?
You can just update this file in **VS Code**, commit it (`git commit -m "Update docs"`), push it, and pull it on the server. That acts as a great test of your new workflow!
```
