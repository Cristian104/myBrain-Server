from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Task
from . import db
from datetime import datetime
import psutil

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

# --- MAIN ROUTES ---


@main.route('/')
@login_required
def dashboard():
    # Fetch tasks for the current user only
    tasks = Task.query.filter_by(
        user_id=current_user.id).order_by(Task.id.desc()).all()
    return render_template('main/dashboard.html', user=current_user, tasks=tasks)


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
    content = data.get('content')
    priority = data.get('priority', 'normal')
    color = data.get('color', '#3b5bdb')

    # Handle Date
    date_str = data.get('date')
    due_date = None
    if date_str:
        try:
            due_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            pass  # Invalid date, just ignore it

    if content:
        new_task = Task(
            content=content,
            priority=priority,
            color=color,
            due_date=due_date,
            author=current_user
        )
        db.session.add(new_task)
        db.session.commit()
        return jsonify({'success': True, 'id': new_task.id})

    return jsonify({'success': False}), 400


@main.route('/api/tasks/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    task = Task.query.get_or_404(id)
    if task.user_id == current_user.id:
        task.complete = not task.complete
        db.session.commit()
        return jsonify({'success': True, 'new_state': task.complete})
    return jsonify({'success': False}), 403


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
