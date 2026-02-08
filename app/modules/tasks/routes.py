from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import date, timedelta, datetime  # ← Added full datetime import
import calendar

from app.extensions import db
from app.models import Task, TaskHistory

# New Blueprint for the separate Tasks/Reminders app
tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')  # Prefix keeps URLs the same (/api/tasks/*)

# --- TASK API ROUTES (UPDATED FOR DATETIME SUPPORT) ---


@tasks_bp.route('/add', methods=['POST'])
@login_required
def add_task():
    data = request.json
    due_datetime = None
    if data.get('datetime'):
        try:
            # JS sends format like '2026-02-08T08:00' or '2026-02-08T08:00:00'
            due_datetime = datetime.fromisoformat(data['datetime'])
        except ValueError:
            try:
                # Fallback: add seconds if missing
                due_datetime = datetime.fromisoformat(data['datetime'] + ':00')
            except ValueError:
                pass  # Invalid format – ignore

    new_task = Task(
        content=data['content'],
        priority=data.get('priority', 'normal'),
        category=data.get('category', 'general'),
        color=data.get('color', '#3b5bdb'),
        recurrence=data.get('recurrence', 'none'),
        is_habit=data.get('is_habit', False),
        due_date=due_datetime,
        user_id=current_user.id  # ← Fixed: Use user_id (matches model column)
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'success': True, 'id': new_task.id})


@tasks_bp.route('/<int:id>/toggle', methods=['POST'])
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

    return jsonify({'success': True, 'new_state': task.complete, 'priority': task.priority, 'new_date_label': new_date_label})


@tasks_bp.route('/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})


@tasks_bp.route('/<int:id>/edit', methods=['POST'])
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

    if data.get('datetime'):
        try:
            task.due_date = datetime.fromisoformat(data['datetime'])
        except ValueError:
            try:
                task.due_date = datetime.fromisoformat(data['datetime'] + ':00')
            except ValueError:
                pass  # Invalid – keep existing due_date

    db.session.commit()
    return jsonify({'success': True})


@tasks_bp.route('/<int:id>/history/add', methods=['POST'])
@login_required
def add_history(id):
    task = Task.query.get_or_404(id)
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    date_str = data.get('date')
    if date_str:
        try:
            history_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            exists = TaskHistory.query.filter_by(
                task_id=task.id, completed_date=history_date).first()
            if not exists:
                new_history = TaskHistory(
                    task_id=task.id, completed_date=history_date, user_id=current_user.id)
                db.session.add(new_history)
                db.session.commit()
                return jsonify({'success': True})
        except ValueError:
            pass
    return jsonify({'success': False})


# Task-specific stats (heatmap/radial)
@tasks_bp.route('/charts')
@login_required
def stats_charts():
    # 1. Radial
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

    # 2. Heatmap (Current Month)
    habits = Task.query.filter_by(user_id=current_user.id, is_habit=True).all()
    heatmap_data = []
    today = date.today()
    first_day = today.replace(day=1)
    last_day_num = calendar.monthrange(today.year, today.month)[1]
    last_day = today.replace(day=last_day_num)
    days_in_month = (last_day - first_day).days + 1

    for habit in habits:
        habit_obj = {'id': habit.id, 'name': habit.content,
                     'color': habit.color, 'data': []}
        history = TaskHistory.query.filter(
            TaskHistory.task_id == habit.id,
            TaskHistory.completed_date >= first_day,
            TaskHistory.completed_date <= last_day).all()
        completed_dates = {h.completed_date.strftime('%Y-%m-%d') for h in history}
        for i in range(days_in_month):
            d = first_day + timedelta(days=i)
            d_str = d.strftime('%Y-%m-%d')
            is_done = d_str in completed_dates
            is_future = d > today
            habit_obj['data'].append({
                'x': i,
                'y': 100 if is_done else 0,
                'real_date': d_str,
                'fillColor': habit.color,
                'is_future': is_future
            })
        heatmap_data.append(habit_obj)

    return jsonify({
        'radial': radial_values,
        'radial_labels': radial_labels,
        'heatmap': heatmap_data
    })