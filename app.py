import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from extensions import db, login_manager
from security import csrf_field, get_csrf_token, validate_csrf


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Trust Render's proxy headers so Flask generates correct HTTPS-aware URLs.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    login_manager.session_protection = 'strong'

    from models import User
    from routes.auth import auth_bp
    from routes.tickets import ticket_bp

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.get('/health')
    def healthcheck():
        return {'status': 'ok'}, 200

    @app.before_request
    def protect_forms():
        validate_csrf()

    @app.context_processor
    def inject_template_helpers():
        return {
            'csrf_field': csrf_field,
            'csrf_token': get_csrf_token,
        }

    @app.after_request
    def apply_security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        return response

    app.register_blueprint(auth_bp)
    app.register_blueprint(ticket_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', '0') == '1',
    )
