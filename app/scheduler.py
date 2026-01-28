from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from datetime import datetime, timedelta, timezone, time
from . import db
from .models import Task, TaskHistory, User
from .telegram_bot import send_telegram_message, send_telegram_photo
from PIL import Image, ImageDraw
import io
import atexit

# ... (Keep generate_habit_image as is) ...


def generate_habit_image(user_id, app):
    """Generates a dot-grid image of your habits."""
    with app.app_context():
        habits = Task.query.filter_by(user_id=user_id, is_habit=True).all()
        if not habits:
            return None

        days_to_show = 14
        dot_size = 20
        gap = 10
        row_height = 40
        width = 160 + (days_to_show * (dot_size + gap))
        height = 60 + (len(habits) * row_height)

        img = Image.new('RGB', (width, height), color='#1A1A1A')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "HABIT TRACKER (14 Days)", fill='#888888')

        today = datetime.now(timezone.utc).date()

        for i, habit in enumerate(habits):
            y_pos = 40 + (i * row_height)
            name = habit.content[:15]
            draw.text((10, y_pos), name, fill='#FFFFFF')
            active_color = habit.color if habit.color else '#2ecc71'

            for d in range(days_to_show):
                check_date = today - timedelta(days=(days_to_show - 1 - d))
                done = TaskHistory.query.filter_by(
                    task_id=habit.id, completed_date=check_date).first()
                x_pos = 160 + (d * (dot_size + gap))
                fill = active_color if done else '#222222'
                draw.ellipse([x_pos, y_pos, x_pos + dot_size,
                             y_pos + dot_size], fill=fill, outline=None)

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf

# --- UPDATED: DAILY RESET LOGIC ---


def reset_daily_tasks(app):
    """Runs at 00:01 AM: Unchecks daily tasks AND moves their due date to Today."""
    with app.app_context():
        print("⏰ Scheduler: Checking for daily tasks to reset...")
        # Find all daily tasks (whether done or not, we ensure they are ready for the new day)
        daily_tasks = Task.query.filter_by(recurrence='daily').all()
        count = 0
        today = datetime.now().date()

        for task in daily_tasks:
            # 1. Uncheck it
            if task.complete:
                task.complete = False
                count += 1

            # 2. IMPORTANT: Update Due Date to TODAY so it shows up in "Today" lists/Bot
            # We preserve the original time if it exists, otherwise default to 00:00
            if task.due_date:
                original_time = task.due_date.time()
                task.due_date = datetime.combine(today, original_time)
            else:
                task.due_date = datetime.combine(today, time.min)

        if count > 0:
            db.session.commit()
            print(f"✅ Scheduler: Reset {count} daily tasks and updated dates.")
        else:
            print("💤 Scheduler: Daily tasks dates updated, no unchecking needed.")

# --- (Keep Notification Logic exactly as is) ---


def check_daily_notifications(app):
    with app.app_context():
        user = User.query.get(1)
        if not user:
            return
        today = datetime.now(timezone.utc).date()
        overdue = Task.query.filter(
            Task.user_id == user.id, Task.complete == False, db.func.date(Task.due_date) < today).all()
        due_today = Task.query.filter(
            Task.user_id == user.id, Task.complete == False, db.func.date(Task.due_date) == today).all()

        if not overdue and not due_today:
            send_telegram_message(
                "<b>☀️ Morning Briefing</b>\n\nNo tasks scheduled for today. Enjoy your freedom! 🏝️")
            return

        msg = "<b>☀️ Morning Briefing</b>\n\n"
        if overdue:
            msg += f"⚠️ <b>{len(overdue)} Overdue:</b>\n"
            for t in overdue:
                msg += f"• {t.content}\n"
        if due_today:
            msg += f"\n📅 <b>{len(due_today)} For Today:</b>\n"
            for t in due_today:
                msg += f"• {t.content}\n"
        send_telegram_message(msg)


def check_daily_summary(app):
    with app.app_context():
        now_utc = datetime.now(timezone.utc)
        today = now_utc.date()
        tomorrow = today + timedelta(days=1)
        completed = Task.query.filter(Task.complete == True, Task.last_completed >= now_utc.replace(
            hour=0, minute=0, second=0, microsecond=0)).all()
        start_tomorrow = datetime.combine(tomorrow, time.min)
        end_tomorrow = datetime.combine(tomorrow, time.max)
        upcoming = Task.query.filter(Task.due_date >= start_tomorrow, Task.due_date <= end_tomorrow, db.or_(
            Task.complete == False, db.and_(Task.complete == True, Task.recurrence != 'none'))).all()

        if not completed and not upcoming:
            return

        msg = "<b>🌙 Daily Closing</b>\n\n"
        if completed:
            msg += f"<b>✅ Achieved Today ({len(completed)})</b>\n"
            for t in completed:
                msg += f"• {t.content}\n"
            msg += "\n"
        else:
            msg += "<i>No tasks completed today.</i>\n\n"

        if upcoming:
            msg += f"<b>🚀 Tomorrow's Focus ({len(upcoming)})</b>\n"
            for t in upcoming:
                icon = "🔥" if t.priority == 'urgent' else "•"
                msg += f"{icon} {t.content}\n"
        else:
            msg += "<i>Nothing scheduled for tomorrow yet. Sleep well! 💤</i>"
        send_telegram_message(msg)


def check_weekly_briefing(app):
    with app.app_context():
        msg = "<b>📅 Weekly Briefing</b>\nHere is your habit consistency:"
        img_buffer = generate_habit_image(1, app)
        if img_buffer:
            send_telegram_photo(msg, img_buffer)
        else:
            send_telegram_message(msg + "\n(No habits found to graph)")

# --- START SCHEDULER ---


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: reset_daily_tasks(app), 'cron', hour=0, minute=1)
    scheduler.add_job(lambda: check_daily_notifications(app), 'cron', hour=8)
    scheduler.add_job(lambda: check_daily_summary(app), 'cron', hour=22)
    scheduler.add_job(lambda: check_weekly_briefing(app),
                      'cron', day_of_week='sun', hour=20)
    scheduler.start()
    print("🚀 Scheduler started: Daily Reset, Morning Brief, Night Summary, Weekly Graph active.")
    atexit.register(lambda: scheduler.shutdown())
