from flask import Flask, session
from app.routes.auth import AuthRoutes
from app.models.database import Database
from config import SECRET_KEY


def create_app():
    app = Flask(__name__)

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

    return app
