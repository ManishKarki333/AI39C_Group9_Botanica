from flask import Flask
from app.routes.auth import AuthRoutes
from app.models.database import Database
from config import SECRET_KEY

def create_app():
    app = Flask(__name__)
    
    # Set secret key from config
    app.config['SECRET_KEY'] = SECRET_KEY

    # Initialize database tables using our Database class
    with app.app_context():
        Database.create_tables()
    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())
    return app