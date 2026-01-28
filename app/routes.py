from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from . import db
from .models import Task, TaskHistory, User
from datetime import datetime, date, timedelta
import psutil
from .scheduler import check_daily_notifications, check_daily_summary, check_weekly_briefing, reset_daily_tasks
import calendar  # <--- NEW IMPORT

main = Blueprint('main', __name__)

# --- BASIC NAVIGATION ---


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.dashboard'))


@main.route('/dashboard')
@login_required
def dashboard():
    # LOGIC FIX:
    # 1. Fetch ALL tasks for user
    # 2. Filter: Show if (Not Complete) OR (Recurring) OR (Completed Today)
    # This hides one-time tasks completed yesterday or before.

    all_tasks = Task.query.filter_by(user_id=current_user.id).order_by(
        Task.complete, Task.due_date).all()

    visible_tasks = []
    today_start = datetime.combine(date.today(), datetime.min.time())

    for t in all_tasks:
        if not t.complete:
            visible_tasks.append(t)
        elif t.recurrence != 'none':
            # Recurring tasks stay visible (usually reset by scheduler, but just in case)
            visible_tasks.append(t)
        else:
            # It's a completed one-time task. Only show if completed TODAY.
            if t.last_completed and t.last_completed >= today_start:
                visible_tasks.append(t)
            # Else: it was completed in the past, so we hide it (archive it).

    return render_template('main/dashboard.html', tasks=visible_tasks, now=datetime.now())


@main.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html')


@main.route('/dev')
@login_required
def dev_panel():
    return render_template('main/dev_panel.html')


# --- API: TASKS ---
# (Keep add_task, toggle_task, delete_task, edit_task, add_history EXACTLY AS THEY WERE)
# I am omitting them here to save space, but DO NOT DELETE THEM from your file.
# ... [Paste existing task API routes here] ...

@main.route('/api/tasks/add', methods=['POST'])
@login_required
def add_task():
    data = request.json
    due_date_val = None
    if data.get('date'):
        try:
            due_date_val = datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            pass

    new_task = Task(
        content=data['content'],
        priority=data.get('priority', 'normal'),
        category=data.get('category', 'general'),
        color=data.get('color', '#3b5bdb'),
        recurrence=data.get('recurrence', 'none'),
        is_habit=data.get('is_habit', False),
        due_date=due_date_val,
        user=current_user
    )

    db.session.add(new_task)
    db.session.commit()
    return jsonify({'success': True, 'id': new_task.id})


@main.route('/api/tasks/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    task.complete = not task.complete
    new_date_label = ""

    if task.complete:
        task.last_completed = datetime.now()
        if task.is_habit:
            today = date.today()
            exists = TaskHistory.query.filter_by(
                task_id=task.id, completed_date=today).first()
            if not exists:
                history = TaskHistory(
                    task_id=task.id, completed_date=today, user_id=current_user.id)
                db.session.add(history)

    db.session.commit()

    if task.due_date:
        days_left = (task.due_date.date() - date.today()).days
        if days_left < 0:
            new_date_label = f"{abs(days_left)}d overdue"
        elif days_left == 0:
            new_date_label = "Today"
        elif days_left == 1:
            new_date_label = "Tomorrow"
        else:
            new_date_label = f"{days_left}d left"

    return jsonify({
        'success': True,
        'new_state': task.complete,
        'priority': task.priority,
        'new_date_label': new_date_label
    })


@main.route('/api/tasks/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})


@main.route('/api/tasks/<int:id>/edit', methods=['POST'])
@login_required
def edit_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    task.content = data['content']
    task.priority = data['priority']
    task.color = data['color']
    task.recurrence = data['recurrence']
    task.category = data['category']
    task.is_habit = data['is_habit']

    if data.get('date'):
        try:
            task.due_date = datetime.strptime(data['date'], '%Y-%m-%d')
        except:
            pass

    db.session.commit()
    return jsonify({'success': True})


@main.route('/api/tasks/<int:id>/history/add', methods=['POST'])
@login_required
def add_history(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.json
    date_str = data.get('date')

    if date_str:
        history_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        exists = TaskHistory.query.filter_by(
            task_id=task.id, completed_date=history_date).first()

        if not exists:
            new_history = TaskHistory(
                task_id=task.id, completed_date=history_date, user_id=current_user.id)
            db.session.add(new_history)
            db.session.commit()
            return jsonify({'success': True})

    return jsonify({'success': False})


@main.route('/api/stats')
@login_required
def get_stats():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    # Versioning trick to auto-refresh UI when data changes
    task_count = Task.query.filter_by(user_id=current_user.id).count()
    history_count = TaskHistory.query.filter_by(
        user_id=current_user.id).count()
    version = task_count + history_count

    return jsonify({'cpu': cpu, 'ram': ram, 'disk': disk, 'data_version': version})

# --- UPDATED CHART DATA (Fixes Bullet Chart Range) ---


@main.route('/api/stats/charts')
@login_required
def stats_charts():
    # 1. Radial Data (Unchanged)
    categories = ['general', 'work', 'personal', 'dev', 'health']
    radial_values = []
    radial_labels = [c.capitalize() for c in categories]

    for cat in categories:
        cat_tasks = Task.query.filter_by(
            user_id=current_user.id, category=cat).all()
        total = len(cat_tasks)
        if total == 0:
            radial_values.append(None)
        else:
            completed = len([t for t in cat_tasks if t.complete])
            percent = int((completed / total) * 100)
            radial_values.append(percent)

    # 2. Heatmap Data (UPDATED FOR CURRENT MONTH)
    habits = Task.query.filter_by(user_id=current_user.id, is_habit=True).all()
    heatmap_data = []

    today = date.today()
    # Calculate First and Last day of Current Month
    first_day = today.replace(day=1)
    last_day_num = calendar.monthrange(today.year, today.month)[1]
    last_day = today.replace(day=last_day_num)

    # Range: 1st to Last Day
    days_in_month = (last_day - first_day).days + 1

    for habit in habits:
        habit_obj = {
            'id': habit.id,
            'name': habit.content,
            'color': habit.color,
            'data': []
        }
        # Fetch history for this month
        history = TaskHistory.query.filter(
            TaskHistory.task_id == habit.id,
            TaskHistory.completed_date >= first_day,
            TaskHistory.completed_date <= last_day
        ).all()
        completed_dates = {h.completed_date.strftime(
            '%Y-%m-%d') for h in history}

        for i in range(days_in_month):
            d = first_day + timedelta(days=i)
            d_str = d.strftime('%Y-%m-%d')
            is_done = d_str in completed_dates

            # Frontend needs to know if this date is in the future
            is_future = d > today

            habit_obj['data'].append({
                'x': i,
                'y': 100 if is_done else 0,
                'real_date': d_str,
                'fillColor': habit.color,
                'is_future': is_future  # Flag for dashboard.js
            })
        heatmap_data.append(habit_obj)

    return jsonify({'radial': radial_values, 'radial_labels': radial_labels, 'heatmap': heatmap_data})

# --- DEV PANEL ROUTES (Keep your existing ones) ---


@main.route('/api/trigger/daily', methods=['POST'])
@login_required
def dev_trigger_daily():
    check_daily_notifications(current_app)
    return jsonify({'success': True, 'message': 'Morning alert triggered!'})


@main.route('/api/test/alert', methods=['POST'])
@login_required
def dev_test_alert():
    check_daily_notifications(current_app)
    return jsonify({'success': True, 'message': 'Urgent alert simulation sent!'})


@main.route('/api/trigger/summary', methods=['POST'])
@login_required
def dev_trigger_summary():
    check_daily_summary(current_app)
    return jsonify({'success': True, 'message': 'Night summary triggered!'})


@main.route('/api/trigger/weekly', methods=['POST'])
@login_required
def dev_trigger_weekly():
    check_weekly_briefing(current_app)
    return jsonify({'success': True, 'message': 'Weekly briefing triggered!'})


@main.route('/api/test/seed', methods=['POST'])
@login_required
def dev_seed_data():
    import random
    tasks = Task.query.filter_by(user_id=current_user.id, is_habit=True).all()
    if not tasks:
        return jsonify({'success': False, 'message': 'No habits found to seed.'})
    today = date.today()
    added_count = 0
    # Seed current month data
    for i in range(30):
        d = today - timedelta(days=i)
        # Don't seed future
        if d > today:
            continue
        for t in tasks:
            if random.random() > 0.5:
                exists = TaskHistory.query.filter_by(
                    task_id=t.id, completed_date=d).first()
                if not exists:
                    h = TaskHistory(task_id=t.id, completed_date=d,
                                    user_id=current_user.id)
                    db.session.add(h)
                    added_count += 1
    db.session.commit()
    return jsonify({'success': True, 'message': f'Seeded {added_count} history entries.'})


@main.route('/api/test/midnight', methods=['POST'])
@login_required
def dev_trigger_midnight():
    reset_daily_tasks(current_app)
    return jsonify({'success': True, 'message': 'Midnight cleanup ran. Daily tasks reset.'})
