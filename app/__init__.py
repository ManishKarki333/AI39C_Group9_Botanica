<<<<<<< HEAD
from flask import Flask, session
from app.routes.auth import AuthRoutes
=======
from flask import Flask, app
from app.routes.auth_routes import AuthRoutes
from app.routes.shop_routes import ShopRoutes
>>>>>>> fc2896550ec8bc13a3dd7735dbbd65a7fd2c7a68
from app.models.database import Database
from config import SECRET_KEY


def create_app():
    app = Flask(__name__)
<<<<<<< HEAD

    app.config['SECRET_KEY'] = SECRET_KEY

    with app.app_context():
        Database.create_tables()

    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())

    @app.context_processor
    def inject_cart_count():
        user_id = session.get("user_id")
        if not user_id:
            return {"cart_count": 0}

        try:
            from app.models.cart_model import CartModel
            cart_model = CartModel()
            cart_count = cart_model.get_cart_count(user_id)
            return {"cart_count": cart_count}
        except Exception as e:
            print("CART ERROR:", e)
            return {"cart_count": 0}
=======
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

    # 2. Register the returned blueprints natively into the app instance context
    app.register_blueprint(auth_router.register())
    app.register_blueprint(shop_router.register())
>>>>>>> fc2896550ec8bc13a3dd7735dbbd65a7fd2c7a68

    return app
