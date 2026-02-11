My Brain Portal
===============

**My Brain Portal** is a personal, secure web dashboard — your "second brain" in one place.Hosted at [mybrain.world](https://mybrain.world), it combines task management, habit tracking, system monitoring, gym logging, and Telegram integration into a single, login-protected hub.

Built with Flask, it's designed for self-hosting with Docker, Nginx reverse proxy, and Cloudflare for SSL/security.

Features
--------

*   **Secure Authentication** — Flask-Login with username/password.
    
*   **Tasks & Reminders** — Full to-do list with:
    
    *   Priorities (normal, high, urgent)
        
    *   Categories & color tags
        
    *   Due dates/times
        
    *   Recurrence (one-time, daily, weekly)
        
    *   Habit tracking with monthly heatmap
        
    *   Overdue & daily Telegram alerts with interactive buttons (Mark Done)
        
*   **Habit Consistency Charts** — Radial category completion rings + 30-day heatmap.
    
*   **System Monitoring** — Real-time CPU, RAM, disk usage.
    
*   **Gym Tracker** — Log routines, exercises, programs (expandable).
    
*   **Telegram Bot Integration** — Morning briefing, overdue alerts, daily summary, weekly habit graph.
    
*   **Scheduler** — APScheduler for timed jobs (daily reset, notifications).
    
*   **Responsive Design** — Bootstrap-based, mobile-friendly.
    

Screenshots
-----------

_(Add screenshots here once available — e.g., dashboard view, task modal, heatmap, Telegram alerts)_

Tech Stack
----------

*   **Backend**: Flask, Flask-SQLAlchemy, Flask-Login, APScheduler
    
*   **Frontend**: Jinja2 templates, vanilla JS, Bootstrap CSS
    
*   **Database**: SQLite (persistent via Docker volume)
    
*   **Deployment**: Docker Compose, Gunicorn
    
*   **Other**: pyTelegramBotAPI, psutil, Pillow
    

Setup & Installation
--------------------

### Prerequisites

*   Docker & Docker Compose
    
*   Git
    
*   Domain with Cloudflare (optional but recommended for SSL/proxy)
    

### Local Development

1.  git clone https://github.com/Cristian104/myBrain-Server.gitcd myBrain-Server
    
2.  python run.pyAccess at [http://localhost:5000](http://localhost:5000)
    

### Production Deployment (Docker)

1.  git clone https://github.com/Cristian104/myBrain-Server.gitcd myBrain-Server
    
2.  SECRET\_KEY=your\_strong\_secret\_hereTELEGRAM\_BOT\_TOKEN=your\_bot\_tokenTELEGRAM\_CHAT\_ID=your\_chat\_id
    
3.  docker compose up -d --build
    
4.  Point domain (mybrain.world) to server IP via Cloudflare proxy.
    
5.  First login: Create user via registration or dev tools.
    

Usage
-----

*   Login at /login
    
*   Dashboard: Add/manage tasks, view stats/charts
    
*   Telegram: Receive alerts, mark tasks done via buttons
    

Deployment Script
-----------------

A custom publishBrain script on the server automates:

*   Git pull
    
*   Smart DB backup (only on changes)
    
*   Docker rebuild
    
*   Telegram notifications
    

Contributing
------------

Feel free to fork and submit PRs! Focus on modularity (new "apps" as blueprints).

License
-------

Personal project — use/modify freely.

_Built with ❤️ by Cristian — your all-in-one personal portal._