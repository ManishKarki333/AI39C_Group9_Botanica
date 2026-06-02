from flask import Blueprint
from app.controllers.auth import AuthController
from app.controllers.shop_controller import ShopController
from app.auth import merchant_required


class AuthRoutes:
    def __init__(self) -> None:
        self.bp = Blueprint("auth", __name__)
        self.controller = AuthController()
        self.shop_controller = ShopController()

    def register(self) -> Blueprint:
        """Register all routes onto the Blueprint and return it."""

        # ── Public pages ──────────────────────────────────────
        self.bp.add_url_rule(
            "/",
            endpoint="home",
            view_func=self.controller.home,
            methods=["GET"],
        )
        self.bp.add_url_rule(
            "/login",
            endpoint="login",
            view_func=self.controller.login,
            methods=["GET", "POST"],
        )
        self.bp.add_url_rule(
            "/register",
            endpoint="register",
            view_func=self.controller.register,
            methods=["GET", "POST"],
        )
        self.bp.add_url_rule(
            "/about",
            endpoint="about",
            view_func=self.controller.about,
            methods=["GET"],
        )
        self.bp.add_url_rule(
            "/contact",
            endpoint="contact",
            view_func=self.controller.contact,
            methods=["GET", "POST"],
        )
        self.bp.add_url_rule(
            "/logout",
            endpoint="logout",
            view_func=self.controller.logout,
            methods=["GET"],
        )

        # ── Merchant-protected pages ──────────────────────────
        self.bp.add_url_rule(
            "/merchant_dashboard",
            endpoint="merchant_dashboard",
            view_func=merchant_required(self.controller.merchant_dashboard),
            methods=["GET"],
        )
        self.bp.add_url_rule(
            "/add_product",
            endpoint="add_product",
            view_func=merchant_required(self.shop_controller.add_product),
            methods=["POST"],
        )

        # ── Shop pages ────────────────────────────────────────
        self.bp.add_url_rule(
            "/shop",
            endpoint="shop",
            view_func=self.shop_controller.shop,
            methods=["GET", "POST"],
        )
        self.bp.add_url_rule(
            "/herb_library",
            endpoint="herb_library",
            view_func=self.shop_controller.herb_library,
            methods=["GET"],
        )
        self.bp.add_url_rule(
            "/herb_details/<int:id>",
            endpoint="herb_details",
            view_func=self.shop_controller.herb_details,
            methods=["GET"],
        )

        return self.bp
