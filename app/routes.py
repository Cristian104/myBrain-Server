from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
import psutil

# Local Imports
from . import db
from .models import User, Task, TaskHistory
from .telegram_bot import send_telegram_message
from app.scheduler import check_daily_notifications, check_weekly_briefing

# --- BLUEPRINT DEFINITIONS ---
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
api = Blueprint('api', __name__)

# --- MAIN ROUTES ---


@main.route('/')
@login_required
def dashboard():
    today = datetime.now(timezone.utc).date()

    # 1. MIDNIGHT RESET LOGIC
    recurring_tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.recurrence != 'none',
        Task.complete == True
    ).all()

    for task in recurring_tasks:
        if task.last_completed and task.last_completed.date() < today:
            task.complete = False
            db.session.commit()

    # 2. SMART SORTING
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(
        Task.complete.asc(),
        Task.priority.desc(),
        Task.due_date.asc()
    ).all()

    return render_template('main/dashboard.html', tasks=tasks, now=datetime.now())


@main.route('/api/stats')
@login_required
def server_stats():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    return jsonify({'cpu': cpu, 'ram': ram, 'disk': disk})


# --- TASK API ROUTES ---

@main.route('/api/tasks/add', methods=['POST'])
@login_required
def add_task():
    data = request.json
    content = data.get('content')
    priority = data.get('priority', 'normal')
    color = data.get('color', '#3b5bdb')
    recurrence = data.get('recurrence', 'none')
    category = data.get('category', 'general')
    is_habit = data.get('is_habit', False)

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
            recurrence=recurrence,
            category=category,
            is_habit=is_habit,
            complete=False,  # Explicitly False on creation
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
    if task.user_id != current_user.id:
        return jsonify({'success': False}), 403

    data = request.json

    if 'content' in data:
        task.content = data['content']
    if 'priority' in data:
        task.priority = data['priority']
    if 'color' in data:
        task.color = data['color']
    if 'recurrence' in data:
        task.recurrence = data['recurrence']
    if 'category' in data:
        task.category = data['category']
    if 'is_habit' in data:
        task.is_habit = data['is_habit']

    if 'date' in data:
        date_str = data['date']
        if date_str:
            try:
                task.due_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                pass
        else:
            task.due_date = None

    db.session.commit()
    return jsonify({'success': True})


@main.route('/api/tasks/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    today = datetime.now(timezone.utc).date()

    # LOGIC: If currently Done -> We are Unchecking it
    if task.complete:
        task.complete = False
        task.last_completed = None

        # ✅ REMOVE HISTORY (Fixes "Active by Default" bug)
        # If I uncheck it today, remove today's dot.
        history_log = TaskHistory.query.filter_by(
            task_id=task.id,
            completed_date=today
        ).first()

        if history_log:
            db.session.delete(history_log)

    # LOGIC: If currently Not Done -> We are Checking it
    else:
        task.complete = True
        task.last_completed = datetime.now(timezone.utc)

        # ✅ ADD HISTORY
        existing_log = TaskHistory.query.filter_by(
            task_id=task.id,
            completed_date=today
        ).first()

        if not existing_log:
            log = TaskHistory(task_id=task.id, completed_date=today)
            db.session.add(log)

    db.session.commit()
    return jsonify({'success': True, 'new_state': task.complete})


@main.route('/api/tasks/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        # 1. Delete all history logs for this task first
        TaskHistory.query.filter_by(task_id=id).delete()

        # 2. Delete the task itself
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 403


# --- CHART DATA ROUTE (THE CRITICAL PART) ---

@main.route('/api/stats/charts')
@login_required
def get_chart_data():
    # 1. RADIAL DATA
    today = datetime.now(timezone.utc).date()
    start_of_week = today - timedelta(days=today.weekday())
    categories = ['general', 'work', 'personal', 'dev', 'health']
    radial_series = []

    for cat in categories:
        completed_weekly = Task.query.filter(
            Task.user_id == current_user.id, Task.category == cat,
            Task.complete == True, Task.last_completed >= start_of_week
        ).count()
        pending = Task.query.filter(
            Task.user_id == current_user.id, Task.category == cat,
            Task.complete == False
        ).count()
        total_weekly = completed_weekly + pending

        percentage = int((completed_weekly / total_weekly)
                         * 100) if total_weekly > 0 else 0
        radial_series.append(percentage)

    # 2. HEATMAP DATA (With Color Injection)
    start_date = today.replace(day=1)
    next_month = today.replace(day=28) + timedelta(days=4)
    end_date = next_month - timedelta(days=next_month.day)

    habit_tasks = Task.query.filter_by(
        user_id=current_user.id, is_habit=True).all()
    heatmap_series = []

    for task in habit_tasks:
        history = TaskHistory.query.filter(
            TaskHistory.task_id == task.id,
            TaskHistory.completed_date >= start_date,
            TaskHistory.completed_date <= end_date
        ).all()
        completed_dates = {h.completed_date for h in history}

        data_points = []
        current = start_date

        # ✅ Get the correct color for this task
        active_color = task.color if task.color else '#2ecc71'

        while current <= end_date:
            if current in completed_dates:
                val = 100
                f_color = active_color  # Done = Task Color
            else:
                val = 0
                f_color = '#1A1A1A'     # Missed = Dark Grey

            date_label = current.strftime("%d")
            data_points.append({
                'x': date_label,
                'y': val,
                'fillColor': f_color  # ✅ Sends color to frontend
            })
            current += timedelta(days=1)

        heatmap_series.append({'name': task.content, 'data': data_points})

    return jsonify({
        'radial': radial_series,
        'radial_labels': [c.capitalize() for c in categories],
        'heatmap': heatmap_series
    })

# --- AUTH & DEV ROUTES ---


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


@main.route('/dev/panel')
@login_required
def dev_panel():
    return render_template('main/dev_panel.html', user=current_user)


@main.route('/api/trigger/daily', methods=['POST'])
@login_required
def trigger_daily():
    check_daily_notifications(current_app._get_current_object())
    return jsonify({'success': True})


@main.route('/api/trigger/weekly', methods=['POST'])
@login_required
def trigger_weekly():
    check_weekly_briefing(current_app._get_current_object())
    return jsonify({'success': True})


@main.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html', user=current_user)
