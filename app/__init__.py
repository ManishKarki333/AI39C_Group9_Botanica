from flask import Flask, app
from app.routes.auth_routes import AuthRoutes
from app.routes.order_routes import OrderRoutes
from app.routes.shop_routes import ShopRoutes
from app.models.database import Database
from config import SECRET_KEY


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY

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
    app.register_blueprint(shop_router.register(), url_prefix='/shop')  # Optional prefix for shop routes
    app.register_blueprint(order_router.register())
    return app
