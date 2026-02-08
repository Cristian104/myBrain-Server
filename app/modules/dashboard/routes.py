from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, date
import psutil

from app.extensions import db
from app.models import Task, TaskHistory  # Still needed for dashboard task query + basic counts
from app.scheduler import check_daily_notifications, check_daily_summary, check_weekly_briefing, reset_daily_tasks

dashboard_bp = Blueprint('dashboard', __name__)

# --- ROUTES ---


@dashboard_bp.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    return redirect(url_for('dashboard.dashboard_view'))


@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    all_tasks = Task.query.filter_by(user_id=current_user.id).order_by(
        Task.complete, Task.due_date).all()
    visible_tasks = []
    today_start = datetime.combine(date.today(), datetime.min.time())

    for t in all_tasks:
        if not t.complete:
            visible_tasks.append(t)
        elif t.recurrence != 'none':
            visible_tasks.append(t)
        else:
            if t.last_completed and t.last_completed >= today_start:
                visible_tasks.append(t)

    return render_template('main/dashboard.html', tasks=visible_tasks, now=datetime.now())


@dashboard_bp.route('/settings')
@login_required
def settings():
    return render_template('main/settings.html')


@dashboard_bp.route('/dev')
@login_required
def dev_panel():
    if current_user.role != 'dev':
        flash("Access Denied: Developer clearance required.", "error")
        return redirect(url_for('dashboard.dashboard_view'))

    return render_template('main/dev_panel.html')

# --- API: BASIC STATS (system + counts) ---


@dashboard_bp.route('/api/stats')
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


# --- DEV PANEL TRIGGERS (kept here as they are dev tools for scheduler) ---


@dashboard_bp.route('/api/trigger/daily', methods=['POST'])
@login_required
def dev_trigger_daily():
    check_daily_notifications(current_app)
    return jsonify({'success': True, 'message': 'Morning alert triggered!'})


@dashboard_bp.route('/api/test/alert', methods=['POST'])
@login_required
def dev_test_alert():
    check_daily_notifications(current_app)
    return jsonify({'success': True, 'message': 'Urgent alert simulation sent!'})


@dashboard_bp.route('/api/trigger/summary', methods=['POST'])
@login_required
def dev_trigger_summary():
    check_daily_summary(current_app)
    return jsonify({'success': True, 'message': 'Night summary triggered!'})


@dashboard_bp.route('/api/trigger/weekly', methods=['POST'])
@login_required
def dev_trigger_weekly():
    check_weekly_briefing(current_app)
    return jsonify({'success': True, 'message': 'Weekly briefing triggered!'})


@dashboard_bp.route('/api/test/seed', methods=['POST'])
@login_required
def dev_seed_data():
    import random
    tasks = Task.query.filter_by(user_id=current_user.id, is_habit=True).all()
    if not tasks:
        return jsonify({'success': False, 'message': 'No habits found.'})
    today = date.today()
    added_count = 0
    for i in range(30):
        d = today - timedelta(days=i)
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


@dashboard_bp.route('/api/test/midnight', methods=['POST'])
@login_required
def dev_trigger_midnight():
    reset_daily_tasks(current_app)
    return jsonify({'success': True, 'message': 'Midnight cleanup ran. Daily tasks reset.'})