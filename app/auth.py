from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from . import db
from sqlalchemy import or_

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 👇 FIX: Matches the <input name="username"> from your HTML
        login_input = request.form.get('username')
        password = request.form.get('password')

        # This logic still works for both!
        # If user types "jorg", it matches username.
        # If user types "jorg@mybrain.com", it matches email.
        user = User.query.filter(
            or_(User.email == login_input, User.username == login_input)
        ).first()

        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('main.dashboard'))
            else:
                flash('Incorrect password, please try again.', category='error')
        else:
            flash('User does not exist.', category='error')

    # 👇 Ensure this path matches your file structure: app/templates/auth/login.html
    return render_template("auth/login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
