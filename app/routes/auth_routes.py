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
        self.bp.route("/about", methods=["GET"])(
            self.controller.about
        )
        self.bp.route("/contact", methods=["GET", "POST"])(
            self.controller.contact
        )
        
        # Dashboard stays under auth management
        self.bp.route("/merchant_dashboard", methods=["GET", "POST"])(
            merchant_required(self.controller.merchant_dashboard)
        )
        
        return self.bp