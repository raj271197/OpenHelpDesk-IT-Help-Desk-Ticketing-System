import re
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from constants import MAX_EMAIL_LENGTH, MAX_NAME_LENGTH, MIN_PASSWORD_LENGTH
from extensions import db
from models import User
from notifications import send_email


auth_bp = Blueprint('auth', __name__)

EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _normalize_email(value):
    return (value or '').strip().lower()


def _normalize_name(value):
    return ' '.join((value or '').split())


def _validate_email(email):
    return bool(email) and len(email) <= MAX_EMAIL_LENGTH and EMAIL_PATTERN.match(email)


@auth_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('ticket.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('ticket.dashboard'))

    form_data = {'email': ''}
    if request.method == 'POST':
        email = _normalize_email(request.form.get('email'))
        password = request.form.get('password') or ''
        form_data['email'] = email

        if not _validate_email(email) or not password:
            flash('Enter a valid email address and password.', 'danger')
            return render_template('login.html', form_data=form_data)

        user = User.query.filter(func.lower(User.email) == email).first()
        if user and check_password_hash(user.password_hash, password):
            session.permanent = True
            session.pop('otp_email', None)
            login_user(user)
            flash('Signed in successfully.', 'success')
            return redirect(url_for('ticket.dashboard'))

        flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html', form_data=form_data)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('ticket.dashboard'))

    form_data = {'name': '', 'email': ''}
    if request.method == 'POST':
        name = _normalize_name(request.form.get('name'))
        email = _normalize_email(request.form.get('email'))
        password = request.form.get('password') or ''
        confirm_password = request.form.get('confirm_password') or ''

        form_data = {'name': name, 'email': email}

        if len(name) < 2 or len(name) > MAX_NAME_LENGTH:
            flash('Enter a full name between 2 and 120 characters.', 'danger')
            return render_template('signup.html', form_data=form_data)

        if not _validate_email(email):
            flash('Enter a valid email address.', 'danger')
            return render_template('signup.html', form_data=form_data)

        if User.query.filter(func.lower(User.email) == email).first():
            flash('Email already registered.', 'warning')
            return render_template('signup.html', form_data=form_data)

        if len(password) < MIN_PASSWORD_LENGTH:
            flash(f'Password must be at least {MIN_PASSWORD_LENGTH} characters long.', 'danger')
            return render_template('signup.html', form_data=form_data)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html', form_data=form_data)

        role = 'admin' if User.query.count() == 0 else 'user'
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('signup.html', form_data=form_data)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    session.pop('otp_email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout', methods=['GET'])
@login_required
def logout_get():
    return redirect(url_for('ticket.dashboard'))


@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    if current_user.is_authenticated:
        return redirect(url_for('ticket.dashboard'))

    email = _normalize_email(request.form.get('email'))
    if not _validate_email(email):
        flash('Enter a valid email address to request an OTP.', 'danger')
        return redirect(url_for('auth.login'))

    user = User.query.filter(func.lower(User.email) == email).first()
    if not user:
        flash('Email not found. Please sign up first.', 'warning')
        return redirect(url_for('auth.login'))

    otp = f'{secrets.randbelow(1_000_000):06d}'
    user.otp_code = generate_password_hash(otp)
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=current_app.config['OTP_EXPIRY_MINUTES'])
    db.session.commit()
    session['otp_email'] = user.email

    delivered = send_email(
        'Your OpenHelpDesk OTP',
        (
            f'Hello {user.name},\n\n'
            f'Your OpenHelpDesk login code is {otp}.\n'
            f'It expires in {current_app.config["OTP_EXPIRY_MINUTES"]} minutes.\n\n'
            'If you did not request this code, you can ignore this email.'
        ),
        user.email,
    )

    if delivered:
        flash(f'OTP sent to {user.email}. Enter it below to continue.', 'info')
    elif current_app.config['SHOW_OTP_IN_FLASH']:
        flash(f'Development OTP for {user.email}: {otp}', 'warning')
    else:
        flash('OTP generated, but email delivery is not configured.', 'warning')

    return redirect(url_for('auth.verify_otp'))


@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('ticket.dashboard'))

    email = session.get('otp_email')
    if not email:
        flash('Request a new OTP to continue.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        otp = (request.form.get('otp') or '').strip()
        user = User.query.filter(func.lower(User.email) == email.lower()).first()

        if (
            user
            and user.otp_code
            and len(otp) == 6
            and user.otp_expires_at
            and user.otp_expires_at > datetime.utcnow()
            and check_password_hash(user.otp_code, otp)
        ):
            session.permanent = True
            login_user(user)
            user.otp_code = None
            user.otp_expires_at = None
            session.pop('otp_email', None)
            db.session.commit()
            flash('OTP verified successfully.', 'success')
            return redirect(url_for('ticket.dashboard'))

        if user and user.otp_expires_at and user.otp_expires_at <= datetime.utcnow():
            user.otp_code = None
            user.otp_expires_at = None
            db.session.commit()
            session.pop('otp_email', None)
            flash('Your OTP has expired. Please request a new one.', 'warning')
            return redirect(url_for('auth.login'))

        flash('Invalid or expired OTP. Please try again.', 'danger')

    return render_template('verify_otp.html', otp_email=email)
