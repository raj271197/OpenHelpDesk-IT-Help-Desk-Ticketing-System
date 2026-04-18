import secrets

from flask import abort, request, session
from markupsafe import Markup, escape


CSRF_SESSION_KEY = '_csrf_token'


def get_csrf_token():
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def csrf_field():
    token = escape(get_csrf_token())
    return Markup(f'<input type="hidden" name="csrf_token" value="{token}">')


def validate_csrf():
    if request.method not in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        return

    expected = session.get(CSRF_SESSION_KEY)
    provided = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')

    if not expected or not provided or not secrets.compare_digest(expected, provided):
        abort(400, description='Invalid CSRF token.')
