from flask import Flask
from app.routes.auth_routes import AuthRoutes
from app.routes.order_routes import OrderRoutes
from app.routes.shop_routes import ShopRoutes
from app.models.database import Database
from config import (
    SECRET_KEY, 
    GOOGLE_CLIENT_ID, 
    SMTP_SERVER, 
    SMTP_PORT, 
    SMTP_EMAIL, 
    SMTP_PASSWORD
)


def create_app():
    app = Flask(__name__)
    
    # Base Configurations Matrix Mapping
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # Inject Third-Party OAuth Variables
    app.config['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID
    
    # Inject Structural Email SMTP Configuration Elements
    app.config['SMTP_SERVER'] = SMTP_SERVER
    app.config['SMTP_PORT'] = SMTP_PORT
    app.config['SMTP_EMAIL'] = SMTP_EMAIL
    app.config['SMTP_PASSWORD'] = SMTP_PASSWORD

    with app.app_context():
        try:
            Database.create_tables()
            print("Database tables verified/created successfully.")
        except Exception as e:
            print(f"Database migration failed during startup: {e}")

    # 1. Instantiate the routing blueprint classes
    auth_router = AuthRoutes()
    shop_router = ShopRoutes()
    order_router = OrderRoutes()

    # 2. Register the returned blueprints natively into the app instance context
    app.register_blueprint(auth_router.register())
    app.register_blueprint(shop_router.register(), url_prefix='/shop')
    app.register_blueprint(order_router.register())
    
    return app
