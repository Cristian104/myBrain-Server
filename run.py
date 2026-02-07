# run.py - Development entry point (CORRECTED VERSION)

from dotenv import load_dotenv
import os

# MUST BE FIRST: Load .env BEFORE any imports from 'app'
load_dotenv(override=True)  # override=True ensures it sets even if system env vars exist

# Debug: Confirm loading worked
token_preview = os.getenv('TELEGRAM_BOT_TOKEN')
if token_preview:
    print(f"🔑 TELEGRAM_BOT_TOKEN loaded successfully: {token_preview[:10]}...{token_preview[-4:]}")
else:
    print("❌ TELEGRAM_BOT_TOKEN is MISSING! Check your .env file path/content.")

chat_id = os.getenv('TELEGRAM_CHAT_ID')
print(f"📩 TELEGRAM_CHAT_ID: {chat_id or 'MISSING!'}")

# NOW import from app (after env vars are loaded)
from app import create_app, db
from app.scheduler import start_scheduler

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if needed
        start_scheduler(app)  # Start scheduler + bot listener

    # Debug mode settings
    app.run(
        debug=True,
        use_reloader=False,  # Prevents double-starting bot/scheduler threads
        host='0.0.0.0',       # Accessible from your network if needed
        port=5000
    )