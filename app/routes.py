from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from . import db
from .models import Task, TaskHistory, User
from datetime import datetime, date, timedelta
import psutil

main = Blueprint('main', __name__)


@main.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('main.dashboard'))


@main.route('/dashboard')
@login_required
def dashboard():
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(
        Task.complete, Task.due_date).all()
    return render_template('main/dashboard.html', tasks=tasks, now=datetime.now())

# --- RESTORED ROUTES ---


@main.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html')


@main.route('/dev')
@login_required
def dev_panel():
    # This matches the endpoint 'main.dev_panel' requested by base.html
    return render_template('main/dev_panel.html')

# --- API: ADD TASK ---


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

# --- API: TOGGLE TASK ---


@main.route('/api/tasks/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    task.complete = not task.complete

    msg = ""
    new_date_label = ""

    if task.complete:
        task.last_completed = datetime.now()
        if task.is_habit:
            today = date.today()
            exists = TaskHistory.query.filter_by(
                task_id=task.id,
                completed_date=today
            ).first()
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

# --- API: DELETE TASK ---


@main.route('/api/tasks/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})

# --- API: EDIT TASK ---


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

# --- API: ADD HISTORY ---


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
            task_id=task.id,
            completed_date=history_date
        ).first()

        if not exists:
            new_history = TaskHistory(
                task_id=task.id, completed_date=history_date, user_id=current_user.id)
            db.session.add(new_history)
            db.session.commit()
            return jsonify({'success': True})

    return jsonify({'success': False})

# --- API: SYSTEM STATS ---


@main.route('/api/stats')
@login_required
def get_stats():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent

    task_count = Task.query.filter_by(user_id=current_user.id).count()
    history_count = TaskHistory.query.filter_by(
        user_id=current_user.id).count()
    version = task_count + history_count

    return jsonify({'cpu': cpu, 'ram': ram, 'disk': disk, 'data_version': version})

# --- API: CHART DATA ---


@main.route('/api/stats/charts')
@login_required
def stats_charts():
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

    habits = Task.query.filter_by(user_id=current_user.id, is_habit=True).all()
    heatmap_data = []

    today = date.today()
    start_date = today - timedelta(days=29)

    for habit in habits:
        habit_obj = {
            'id': habit.id,
            'name': habit.content,
            'color': habit.color,
            'data': []
        }

        history = TaskHistory.query.filter(
            TaskHistory.task_id == habit.id,
            TaskHistory.completed_date >= start_date
        ).all()

        completed_dates = {h.completed_date.strftime(
            '%Y-%m-%d') for h in history}

        for i in range(30):
            d = start_date + timedelta(days=i)
            d_str = d.strftime('%Y-%m-%d')
            is_done = d_str in completed_dates

            habit_obj['data'].append({
                'x': i,
                'y': 100 if is_done else 0,
                'real_date': d_str,
                'fillColor': habit.color
            })

        heatmap_data.append(habit_obj)

    return jsonify({
        'radial': radial_values,
        'radial_labels': radial_labels,
        'heatmap': heatmap_data
    })
