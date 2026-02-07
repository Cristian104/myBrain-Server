import os
import telebot
from . import state
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import current_app
import threading
import time
from app.extensions import db
from .models import Task, TaskHistory
from datetime import datetime, timezone

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

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

    # --- FIX: Force Fresh Database Connection ---
    # This clears the "stale" session so we see new tasks created by the website
    db.session.remove()
    # ------------------------------------------

    action, task_id = call.data.split('_')

    try:
        # Acknowledge the click (stops the button from loading/spinning)
        bot.answer_callback_query(call.id, "Processing...")

        task = Task.query.get(int(task_id))

        if not task:
            # If we STILL can't find it, it's genuinely gone
            bot.send_message(call.message.chat.id,
                             "⚠️ Task not found (maybe deleted?).")
            return

        if action == "done":
            # 1. Update DB
            task.complete = True
            task.last_completed = datetime.now(timezone.utc)

            # Habit History Logic
            if task.is_habit:
                today = datetime.now(timezone.utc).date()
                exists = TaskHistory.query.filter_by(
                    task_id=task.id, completed_date=today).first()
                if not exists:
                    h = TaskHistory(task_id=task.id,
                                    completed_date=today, status='completed')
                    db.session.add(h)

            db.session.commit()

            # 2. SIGNAL THE CHANGE (Auto-Refresh Dashboard)
            from . import state
            state.touch()

            # 3. Update the Message
            new_text = f"✅ <b>COMPLETED:</b>\n{task.content}"
            bot.edit_message_text(chat_id=call.message.chat.id,
                                  message_id=call.message.message_id, text=new_text, parse_mode='HTML')

        elif action == "snooze":
            bot.send_message(call.message.chat.id,
                             "💤 Snooze not implemented yet.")

    except Exception as e:
        print(f"❌ Button Error: {e}")
        bot.send_message(call.message.chat.id, f"Error: {str(e)}")
