from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import or_

# Absolute imports (Correct)
from app.models import User
from app.extensions import db

# 👇 CHANGE 1: Rename variable to 'auth_bp' to match __init__.py
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter(
            or_(User.email == login_input, User.username == login_input)
        ).first()

        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)

                # 👇 CHANGE 2: Point to the new 'dashboard' blueprint
                # 'dashboard' is the blueprint name, 'dashboard_view' is the function name
                return redirect(url_for('dashboard.dashboard_view'))
            else:
                flash('Incorrect password, please try again.', category='error')
        else:
            flash('User does not exist.', category='error')

    return render_template("auth/login.html", user=current_user)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    # This remains 'auth.login' because we named the Blueprint 'auth' above
    return redirect(url_for('auth.login'))
