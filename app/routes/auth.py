from flask import Blueprint
from app.controllers.auth import AuthController
from app.controllers.shop_controller import ShopController
from app.controllers.cart_controller import CartController
from app.auth import merchant_required


class AuthRoutes:
    def __init__(self):
        self.auth_controller = AuthController()
        self.shop_controller = ShopController()
        self.cart_controller = CartController()

    def register(self):
        auth_bp = Blueprint("auth", __name__)

        # Public routes
        auth_bp.add_url_rule("/", view_func=self.auth_controller.home, methods=["GET"], endpoint="home")
        auth_bp.add_url_rule("/login", view_func=self.auth_controller.login, methods=["GET", "POST"], endpoint="login")
        auth_bp.add_url_rule("/register", view_func=self.auth_controller.register, methods=["GET", "POST"], endpoint="register")
        auth_bp.add_url_rule("/about", view_func=self.auth_controller.about, methods=["GET"], endpoint="about")
        auth_bp.add_url_rule("/contact", view_func=self.auth_controller.contact, methods=["GET", "POST"], endpoint="contact")
        auth_bp.add_url_rule("/logout", view_func=self.auth_controller.logout, methods=["GET"], endpoint="logout")

        # Shop routes
        auth_bp.add_url_rule("/shop", view_func=self.shop_controller.shop, methods=["GET", "POST"], endpoint="shop")
        auth_bp.add_url_rule("/herb_library", view_func=self.shop_controller.herb_library, methods=["GET"], endpoint="herb_library")
        auth_bp.add_url_rule("/herb_details/<int:id>", view_func=self.shop_controller.herb_details, methods=["GET"], endpoint="herb_details")

        # Merchant routes
        auth_bp.add_url_rule(
            "/merchant_dashboard",
            view_func=merchant_required(self.auth_controller.merchant_dashboard),
            methods=["GET"],
            endpoint="merchant_dashboard"
        )

        auth_bp.add_url_rule(
            "/add_product",
            view_func=merchant_required(self.shop_controller.add_product),
            methods=["POST"],
            endpoint="add_product"
        )

        # Cart routes
        auth_bp.add_url_rule("/cart", view_func=self.cart_controller.view_cart, methods=["GET"], endpoint="view_cart")
        auth_bp.add_url_rule("/cart/add/<int:herb_id>", view_func=self.cart_controller.add_to_cart, methods=["POST"], endpoint="add_to_cart")
        auth_bp.add_url_rule("/cart/update/<int:item_id>", view_func=self.cart_controller.update_cart, methods=["POST"], endpoint="update_cart")
        auth_bp.add_url_rule("/cart/remove/<int:item_id>", view_func=self.cart_controller.remove_from_cart, methods=["POST"], endpoint="remove_from_cart")

        return auth_bp
