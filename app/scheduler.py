from apscheduler.schedulers.background import BackgroundScheduler
from app import db
from app.models import Task
from app.telegram_bot import send_telegram_message
from datetime import datetime, timedelta
import pytz
import atexit

TZ_POLAND = pytz.timezone('Europe/Warsaw')


def format_list_message(header_emoji, context_str, tasks):
    """
    Helper to format messages 'Widget-First' style.
    Preview: "Buy Milk (+2) :: Good Morning..."
    """
    count = len(tasks)
    if count == 0:
        return None

    # THE WIDGET TRICK: Put the first task name right at the start
    first_task = tasks[0].content

    if count == 1:
        # Single Task: "Buy Milk :: Context"
        preview = f"{first_task}"
        body = f"• {first_task}"
    else:
        # Multiple: "Buy Milk (+2) :: Context"
        preview = f"{first_task} (+{count-1})"
        body = "\n".join([f"• {t.content}" for t in tasks])

    return f"{preview} :: {header_emoji} {context_str}\n\n{body}"


def check_daily_notifications(app):
    """ Runs Daily at 8:00 AM """
    with app.app_context():
        now = datetime.now(TZ_POLAND)
        today = now.date()
        tomorrow = today + timedelta(days=1)

        active_tasks = Task.query.filter_by(complete=False).all()

        tasks_today = [
            t for t in active_tasks if t.due_date and t.due_date.date() == today]

        # 1. TODAY'S TASKS
        if tasks_today:
            msg = format_list_message("🌅", "Today's Agenda", tasks_today)
            send_telegram_message(msg)

        # 2. OVERDUE (Gentle Nudge)
        overdue = [t for t in active_tasks if t.due_date and t.due_date.date(
        ) < today and t.priority == 'normal']
        if overdue:
            # Only show if > 3 days late to avoid spam, or just show count
            pass  # Skipping for brevity as requested, focusing on Today/Tomorrow


def check_nightly_reminder(app):
    """ Runs Daily at 10:00 PM (Tomorrow's Preview) """
    with app.app_context():
        now = datetime.now(TZ_POLAND)
        tomorrow = now.date() + timedelta(days=1)

        active_tasks = Task.query.filter_by(complete=False).all()
        tasks_tomorrow = [
            t for t in active_tasks if t.due_date and t.due_date.date() == tomorrow]

        if tasks_tomorrow:
            msg = format_list_message("🌙", "Tomorrow's Plan", tasks_tomorrow)
            send_telegram_message(msg)


def check_weekly_briefing(app):
    """ Runs Sunday at 8:00 PM """
    with app.app_context():
        now = datetime.now(TZ_POLAND)
        today = now.date()
        # ISO Week number
        week_num = now.isocalendar()[1]
        next_week_num = week_num + 1

        # Get tasks for next 7 days
        next_sunday = today + timedelta(days=7)
        active_tasks = Task.query.filter_by(complete=False).all()

        upcoming = []
        for t in active_tasks:
            if t.due_date and today < t.due_date.date() <= next_sunday:
                upcoming.append(t)

        if not upcoming:
            return

        # Sort by date
        upcoming.sort(key=lambda x: x.due_date)

        # Build the list string
        task_list_str = ""
        current_day = None

        for t in upcoming:
            day_name = t.due_date.strftime('%A')  # e.g., "Monday"
            if day_name != current_day:
                task_list_str += f"\n📅 *{day_name}*\n"
                current_day = day_name
            task_list_str += f"• {t.content}\n"

        # Explicit Title as requested
        header = f"📅 *Weekly Briefing — Week {next_week_num}*"
        msg = f"{header}\n{task_list_str}"
        send_telegram_message(msg)


def start_scheduler(app):
    scheduler = BackgroundScheduler(timezone=TZ_POLAND)

    # 1. Morning (8:00 AM) - Today's Tasks
    scheduler.add_job(lambda: check_daily_notifications(app),
                      trigger="cron", hour=8, minute=0)

    # 2. Night (10:00 PM) - Tomorrow's Tasks
    scheduler.add_job(lambda: check_nightly_reminder(app),
                      trigger="cron", hour=22, minute=0)

    # 3. Weekly (Sunday 8:00 PM)
    scheduler.add_job(lambda: check_weekly_briefing(
        app), trigger="cron", day_of_week='sun', hour=20, minute=0)

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
