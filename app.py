import os
from flask import Flask
from extensions import db, login_manager
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
basedir = os.path.abspath(os.path.dirname(__file__))

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def create_app():
    with app.app_context():
        from routes.auth import auth_bp
        from routes.tickets import ticket_bp
        app.register_blueprint(auth_bp)
        app.register_blueprint(ticket_bp)
        db.create_all()
    return app

if __name__ == '__main__':
    create_app()
    app.run(debug=True)
