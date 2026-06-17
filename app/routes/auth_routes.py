from flask import Blueprint
from app.controllers.auth import AuthController
from app.auth import merchant_required


class AuthRoutes:
    def __init__(self):
        # Keeps this blueprint focused strictly on authentication and baseline utilities
        self.bp = Blueprint("auth", __name__)
        self.controller = AuthController()

    def register(self):
        self.bp.route("/", methods=["GET", "POST"])(
            self.controller.home
        )
        self.bp.route("/login", methods=["GET", "POST"])(
            self.controller.login
        )
        self.bp.route("/register", methods=["GET", "POST"])(
            self.controller.register
        )
        self.bp.route("/logout", methods=["GET", "POST"])(
            self.controller.logout
        )
        self.bp.route("/profile", methods=["GET", "POST"])(
            self.controller.profile
        )
        self.bp.route("/deactivate_account", methods=["POST"])(
            self.controller.deactivate_account
        )
        self.bp.route("/delete_account", methods=["POST"])(
            self.controller.delete_account
        )
        self.bp.route("/about", methods=["GET"])(
            self.controller.about
        )
        self.bp.route("/contact", methods=["GET", "POST"])(
            self.controller.contact
        )
        self.bp.route("/google_login", methods=["POST"])(
            self.controller.google_login
        )
        self.bp.route("/forgot_password", methods=["GET", "POST"])(
            self.controller.forgot_password
        )
        self.bp.route("/verify_otp", methods=["GET", "POST"])(
            self.controller.verify_otp
        )
        self.bp.route("/reset_password", methods=["GET", "POST"])(
            self.controller.reset_password
        )
        self.bp.route("/faq", methods=["GET"])(
            self.controller.faq
        )

        # Dashboard stays under auth management
        self.bp.route("/merchant_dashboard", methods=["GET", "POST"])(
            merchant_required(self.controller.merchant_dashboard)
        )

        return self.bp
