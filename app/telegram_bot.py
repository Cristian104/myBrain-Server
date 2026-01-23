import telebot
from . import state
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import current_app
import threading
import time
from . import db
from .models import Task, TaskHistory
from datetime import datetime, timezone

# --- CONFIGURATION ---
# (Replace with your actual token/chat_id or load from config)
BOT_TOKEN = "8420186537:AAHeaf9XcXywWBZ9mZ9tD6q9kSRxzvij3Ts"
CHAT_ID = "7585332236"

# Initialize the Bot
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)


def start_bot_listener(app):
    """Starts the bot polling loop in a separate background thread."""
    def listener_loop():
        # We need to manually push the app context since this is a new thread
        with app.app_context():
            print("🤖 Bot Listener Started...")
            try:
                # This infinite loop listens for clicks
                bot.infinity_polling(timeout=10, long_polling_timeout=5)
            except Exception as e:
                print(f"❌ Bot Crash: {e}")

    # Daemon thread dies when the main server stops
    thread = threading.Thread(target=listener_loop, daemon=True)
    thread.start()

# --- SENDING MESSAGES ---


def send_telegram_message(message):
    """Standard text message (no buttons)."""
    try:
        bot.send_message(CHAT_ID, message, parse_mode='HTML')
    except Exception as e:
        print(f"❌ Telegram Send Error: {e}")


def send_telegram_photo(caption, image_buffer):
    """Sends an image."""
    try:
        bot.send_photo(CHAT_ID, photo=image_buffer,
                       caption=caption, parse_mode='HTML')
    except Exception as e:
        print(f"❌ Telegram Photo Error: {e}")


def send_task_alert(task):
    """Sends a Task Alert with Action Buttons."""
    msg = f"⚠️ <b>Urgent Task Overdue!</b>\n\n{task.content}"

    # Create the Keyboard (Buttons)
    markup = InlineKeyboardMarkup()
    markup.row_width = 2

    # Button 1: Mark Done
    btn_done = InlineKeyboardButton(
        "✅ Mark Done", callback_data=f"done_{task.id}")
    # Button 2: Snooze (Optional Future Feature)
    btn_snooze = InlineKeyboardButton(
        "💤 Snooze 1h", callback_data=f"snooze_{task.id}")

    markup.add(btn_done, btn_snooze)

    try:
        bot.send_message(CHAT_ID, msg, parse_mode='HTML', reply_markup=markup)
    except Exception as e:
        print(f"❌ Telegram Alert Error: {e}")

# --- HANDLING CLICKS (CALLBACKS) ---


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    """This function runs when you click a button."""

    # "done_123" -> action="done", task_id="123"
    action, task_id = call.data.split('_')

    # We need to use the Flask Application Context to access the DB
    # (Note: 'current_app' won't work here directly, we rely on the thread context)
    # TRICK: We passed the app context in 'start_bot_listener', but 'telebot'
    # handles threads differently. We will re-import create_app or use a localized DB approach.
    # SIMPLIFICATION for now: We assume the thread has access if set up correctly.

    # Ideally, we pass the 'app' object to the bot handler, but decorators make that hard.
    # WORKAROUND: Import 'db' and push context manually if needed.
    # For now, let's try standard access.

    try:
        # Acknowledge the click (stops the button from loading/spinning)
        bot.answer_callback_query(call.id, "Processing...")

        task = Task.query.get(int(task_id))

        if not task:
            bot.send_message(CHAT_ID, "⚠️ Task not found (maybe deleted?).")
            return

        if action == "done":
            # 1. Update DB
            task.complete = True
            task.last_completed = datetime.now(timezone.utc)

            # (Optional) Add to history if it's a habit
            if task.is_habit:
                today = datetime.now(timezone.utc).date()
                exists = TaskHistory.query.filter_by(
                    task_id=task.id, completed_date=today).first()
                if not exists:
                    h = TaskHistory(task_id=task.id,
                                    completed_date=today, status='completed')
                    db.session.add(h)

            db.session.commit()
            state.touch()

            # 2. Update the Message (Remove buttons, show success)
            new_text = f"✅ <b>COMPLETED:</b>\n{task.content}"
            bot.edit_message_text(
                chat_id=CHAT_ID, message_id=call.message.message_id, text=new_text, parse_mode='HTML')

        elif action == "snooze":
            bot.send_message(
                CHAT_ID, "💤 Snooze not implemented yet, but good try!")

    except Exception as e:
        print(f"❌ Button Error: {e}")
        # In case of DB context error, we might need a safer app access strategy
        bot.send_message(CHAT_ID, f"Error: {str(e)}")
