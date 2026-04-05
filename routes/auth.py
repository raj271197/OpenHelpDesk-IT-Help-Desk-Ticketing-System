import random
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('ticket.dashboard'))
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('ticket.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('ticket.dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('ticket.dashboard'))
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'warning')
            return redirect(url_for('auth.signup'))
        role = 'admin' if User.query.count() == 0 else 'user'
        hashed_password = generate_password_hash(password)
        user = User(name=name, email=email, password_hash=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Email not found. Please sign up first.', 'warning')
        return redirect(url_for('auth.login'))
    otp = f"{random.randint(100000, 999999)}"
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    session['otp_email'] = email
    flash(f'OTP generated for {email}. Enter it below to continue.', 'info')
    return redirect(url_for('auth.verify_otp'))

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('ticket.dashboard'))
    if request.method == 'POST':
        otp = request.form.get('otp')
        email = session.get('otp_email')
        user = User.query.filter_by(email=email).first() if email else None
        if user and user.otp_code == otp and user.otp_expires_at and user.otp_expires_at > datetime.utcnow():
            login_user(user)
            user.otp_code = None
            user.otp_expires_at = None
            db.session.commit()
            return redirect(url_for('ticket.dashboard'))
        flash('Invalid or expired OTP. Please try again.', 'danger')
    return render_template('verify_otp.html')
