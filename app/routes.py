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

    # 2. SMART QUERY
    tasks = Task.query.filter(
        Task.user_id == current_user.id,
        db.or_(
            Task.complete == False,
            db.and_(Task.complete == True, db.func.date(
                Task.last_completed) == today)
        )
    ).order_by(
        Task.complete.asc(),
        Task.due_date.asc(),
        Task.priority.desc()
    ).all()

    return render_template('main/dashboard.html', tasks=tasks, now=datetime.now())

# --- NEW ROUTE FOR HABIT BACKFILLING ---


@main.route('/api/tasks/<int:id>/history/add', methods=['POST'])
@login_required
def add_task_history(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'success': False}), 403

    data = request.json
    date_str = data.get('date')

    if not date_str:
        return jsonify({'success': False}), 400

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        exists = TaskHistory.query.filter_by(
            task_id=task.id, completed_date=target_date).first()

        if not exists:
            log = TaskHistory(task_id=task.id, completed_date=target_date)
            db.session.add(log)
            db.session.commit()
            return jsonify({'success': True})
        else:
            return jsonify({'success': True, 'message': 'Already marked'})

    except ValueError:
        return jsonify({'success': False}), 400


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
            content=content, priority=priority, color=color, recurrence=recurrence,
            category=category, is_habit=is_habit, complete=False, due_date=due_date,
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

    # 1. UNCHECKING (Undo)
    if task.complete:
        task.complete = False
        task.last_completed = None

        # If I uncheck a Daily task, bring date back to TODAY
        if task.recurrence == 'daily':
            task.due_date = datetime.now(timezone.utc)

        history_log = TaskHistory.query.filter_by(
            task_id=task.id, completed_date=today).first()
        if history_log:
            db.session.delete(history_log)

    # 2. CHECKING (Done)
    else:
        task.complete = True
        task.last_completed = datetime.now(timezone.utc)

        # Move Date Forward instantly
        if task.recurrence == 'daily':
            task.due_date = datetime.now(timezone.utc) + timedelta(days=1)
        elif task.recurrence == 'weekly':
            task.due_date = datetime.now(timezone.utc) + timedelta(weeks=1)

        existing_log = TaskHistory.query.filter_by(
            task_id=task.id, completed_date=today).first()
        if not existing_log:
            log = TaskHistory(task_id=task.id, completed_date=today)
            db.session.add(log)

    db.session.commit()

    # ✅ Calculate New Date Label for Frontend
    date_label = ""
    if task.due_date:
        delta = (task.due_date.date() - today).days
        if delta < 0:
            date_label = f"{abs(delta)}d overdue"
        elif delta == 0:
            date_label = "Today"
        elif delta == 1:
            date_label = "Tomorrow"
        else:
            date_label = f"{delta}d left"

    return jsonify({
        'success': True,
        'new_state': task.complete,
        'new_date_label': date_label,
        'priority': task.priority
    })


@main.route('/api/tasks/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        TaskHistory.query.filter_by(task_id=id).delete()
        db.session.delete(task)
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False}), 403

# --- CHART DATA ROUTE ---


@main.route('/api/stats/charts')
@login_required
def get_chart_data():
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

    # HEATMAP
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
        active_color = task.color if task.color else '#2ecc71'

        while current <= end_date:
            if current in completed_dates:
                val = 100
                f_color = active_color
            else:
                val = 0
                f_color = '#1A1A1A'

            date_label = current.strftime("%d")
            data_points.append({
                'x': date_label,
                'y': val,
                'fillColor': f_color,
                'real_date': current.strftime("%Y-%m-%d")
            })
            current += timedelta(days=1)

        heatmap_series.append({
            'name': task.content,
            'id': task.id,
            'color': active_color,  # ✅ SENDING REAL COLOR FOR CLICKING
            'data': data_points
        })

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


@main.route('/api/test/seed', methods=['POST'])
@login_required
def seed_test_data():
    today = datetime.now(timezone.utc).date()
    test_tasks = [
        {'content': '🔥 Test: Urgent', 'priority': 'urgent', 'category': 'dev',
            'delta': -2, 'color': '#e74c3c', 'habit': False},
        {'content': '🧘 Test: Habit', 'priority': 'normal',
            'category': 'health', 'delta': 0, 'color': '#f1c40f', 'habit': True}
    ]
    for t in test_tasks:
        due = today + timedelta(days=t['delta'])
        task = Task(content=t['content'], priority=t['priority'], category=t['category'], color=t['color'], due_date=datetime.combine(
            due, datetime.min.time()), is_habit=t['habit'], complete=False, author=current_user)
        db.session.add(task)
    db.session.commit()
    return jsonify({'success': True})


@main.route('/api/test/midnight', methods=['POST'])
@login_required
def simulate_midnight():
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    tasks = Task.query.filter_by(user_id=current_user.id, complete=True).all()
    for t in tasks:
        t.last_completed = yesterday
    db.session.commit()
    return jsonify({'success': True})


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
