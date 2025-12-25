from flask import Flask
from .database import init_db

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key'

    init_db()

    from .routes import main
    app.register_blueprint(main)

    from .auth import auth
    app.register_blueprint(auth)

    from .profile import profile
    app.register_blueprint(profile)

    from .admin import admin
    app.register_blueprint(admin)

    from .member import member
    app.register_blueprint(member)

    return app