from flask import Flask
from dotenv import load_dotenv
import os
from .database import init_db

def create_app():
    load_dotenv()  # Load .env file

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

    app.config['PERMANENT_SESSION_LIFETIME'] = 14400  # 4 hours

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