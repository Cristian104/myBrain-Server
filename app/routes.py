from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
import psutil

# Local Imports
from . import db
from .models import User, Task
from .telegram_bot import send_telegram_message
from app.scheduler import check_daily_notifications, check_weekly_briefing

# --- BLUEPRINT DEFINITIONS ---
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)  # <--- This line is now active again!

# --- MAIN ROUTES ---


@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(
        user_id=current_user.id
    ).order_by(Task.id.desc()).all()

    return render_template(
        'main/dashboard.html',
        user=current_user,
        tasks=tasks,
        now=datetime.now()
    )


@main.route('/api/stats')
@login_required
def server_stats():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    return jsonify({'cpu': cpu, 'ram': ram, 'disk': disk})

# --- TASK API ROUTES (NEW) ---


@main.route('/api/tasks/add', methods=['POST'])
@login_required
def add_task():
    data = request.json
    # ... existing content/priority/color extraction ...
    content = data.get('content')
    priority = data.get('priority', 'normal')
    color = data.get('color', '#3b5bdb')
    recurrence = data.get('recurrence', 'none')  # <--- Get it

    # --- NEW: Get Category ---
    category = data.get('category', 'general')

    # ... date logic ...
    date_str = data.get('date')
    due_date = None
    if date_str:
        try:
            due_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            pass

    if content:
        new_task = Task(
            content=content,
            priority=priority,
            color=color,
            recurrence=recurrence,  # <--- Save it
            category=category,  # <--- Add this
            due_date=due_date,
            author=current_user
        )
        db.session.add(new_task)
        db.session.commit()
        return jsonify({'success': True, 'id': new_task.id})
    return jsonify({'success': False}), 400


@main.route('/api/tasks/<int:id>/edit', methods=['POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)

    # 1. Security Check
    if task.user_id != current_user.id:
        return jsonify({'success': False}), 403

    data = request.json

    # 2. Update Standard Fields
    if 'content' in data:
        task.content = data['content']
    if 'priority' in data:
        task.priority = data['priority']
    if 'color' in data:
        task.color = data['color']
    if 'recurrence' in data:
        task.recurrence = data['recurrence']

    # --- NEW: Update Category ---
    if 'category' in data:
        task.category = data['category']
    # ----------------------------

    # 3. Update Date (Cleaned up logic)
    if 'date' in data:
        date_str = data['date']
        if date_str:
            try:
                # Expecting YYYY-MM-DD
                task.due_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                # If date format is wrong, ignore or handle error
                pass
        else:
            # If empty string sent, clear the due date
            task.due_date = None

    # 4. Save to DB
    db.session.commit()
    return jsonify({'success': True})

    db.session.commit()
    return jsonify({'success': True})

    # Handle Date clearing or updating
    if 'date' in data:
        date_str = data['date']
        if date_str:
            try:
                task.due_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                pass
        else:
            task.due_date = None  # Clear date if empty string sent

    db.session.commit()
    return jsonify({'success': True})


# ... imports ...


@main.route('/api/tasks/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'success': False}), 403

    # Toggle the status
    task.complete = not task.complete
    new_state = task.complete

    db.session.commit()  # Save the completion of the current task

    # --- RECURRING LOGIC ---
    # If we just marked it COMPLETE and it has recurrence
    if new_state and task.recurrence == 'weekly':
        # Create the next instance
        next_due = None
        if task.due_date:
            next_due = task.due_date + timedelta(days=7)

        new_task = Task(
            content=task.content,
            priority=task.priority,
            color=task.color,
            due_date=next_due,
            recurrence='weekly',  # Keep the chain going
            user_id=current_user.id
        )
        db.session.add(new_task)
        db.session.commit()

        # Optional: Notify user via Telegram that next week's task is queued?
        # For now, let's keep it silent.

    return jsonify({'success': True, 'new_state': new_state})


@main.route('/api/tasks/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 403


# --- AUTH ROUTES ---

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Access Denied: Invalid credentials')
    return render_template('auth/login.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@main.route('/api/test-telegram')
@login_required
def test_telegram():
    send_telegram_message(
        "✅ *System Test*\nYour dashboard connection is active.")
    return jsonify({'success': True})

# --- DEV PANEL ROUTES ---


@main.route('/dev/panel')
@login_required
def dev_panel():
    return render_template('main/dev_panel.html', user=current_user)


@main.route('/api/trigger/daily', methods=['POST'])
@login_required
def trigger_daily():
    # Force run the daily logic
    check_daily_notifications(current_app._get_current_object())
    return jsonify({'success': True, 'message': 'Daily notifications sent!'})


@main.route('/api/trigger/weekly', methods=['POST'])
@login_required
def trigger_weekly():
    # Force run the weekly logic
    check_weekly_briefing(current_app._get_current_object())  # <--- Updated
    return jsonify({'success': True, 'message': 'Weekly briefing sent!'})

# app/routes.py


@main.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html', user=current_user)
