from flask import Flask
from app.routes.auth import AuthRoutes
from app.models.database import Database
from config import SECRET_KEY


def create_app():
    app = Flask(__name__)
    Database.create_tables()
    # Set secret key from config
    app.config['SECRET_KEY'] = SECRET_KEY

    # Import and register the blueprints
    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())

    return app
