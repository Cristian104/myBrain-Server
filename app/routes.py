from flask import Blueprint, render_template, redirect, url_for, jsonify, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db
import psutil

# Define both Blueprints
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

# --- MAIN ROUTES ---


@main.route('/')
@login_required
def dashboard():
    return render_template('main/dashboard.html', user=current_user)


@main.route('/api/stats')
@login_required
def server_stats():
    # 1. CPU Usage
    cpu = psutil.cpu_percent(interval=1)

    # 2. RAM Usage
    ram = psutil.virtual_memory()
    ram_percent = ram.percent

    # 3. Disk Usage
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent

    return jsonify({
        'cpu': cpu,
        'ram': ram_percent,
        'disk': disk_percent
    })

# --- AUTH ROUTES ---


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # SECURE CHECK: Use the check_password() method
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
