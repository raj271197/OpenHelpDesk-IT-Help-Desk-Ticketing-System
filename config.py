import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / 'instance'
INSTANCE_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / '.env')


def _get_bool_env(key, default=False):
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _get_database_url():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Normalize older Postgres URLs for SQLAlchemy compatibility.
        if database_url.startswith('postgres://'):
            return database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    return f"sqlite:///{(INSTANCE_DIR / 'helpdesk.db').as_posix()}"


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'super-secret-key')
    SQLALCHEMY_DATABASE_URI = _get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {'pool_pre_ping': True}
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = _get_bool_env('MAIL_USE_TLS', default=True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    SESSION_COOKIE_SECURE = _get_bool_env(
        'SESSION_COOKIE_SECURE',
        default=os.getenv('RENDER') == 'true',
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    PREFERRED_URL_SCHEME = 'https' if SESSION_COOKIE_SECURE else 'http'
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', 10))
    SHOW_OTP_IN_FLASH = _get_bool_env(
        'SHOW_OTP_IN_FLASH',
        default=os.getenv('RENDER') != 'true',
    )
