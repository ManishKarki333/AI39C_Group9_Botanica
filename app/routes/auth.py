from flask import Blueprint
from app.controllers.auth import AuthController
from app.controllers.shop_controller import ShopController
from app.auth import login_required, admin_required, merchant_required 

class AuthRoutes:
    def __init__(self):
        self.bp = Blueprint("auth",__name__)
        self.controller = AuthController()
        self.shop_controller = ShopController()

    def register(self):
        self.bp.route("/",methods=["GET", "POST"])(
            self.controller.home
        )
        self.bp.route("/login",methods=["GET", "POST"])(
            self.controller.login
        )
        self.bp.route("/register",methods=["GET", "POST"])(
            self.controller.register
        )
        self.bp.route("/about",methods=["GET", "POST"])(
            self.controller.about
        )
        self.bp.route("/contact",methods=["GET", "POST"])(
            self.controller.contact
        )
        self.bp.route("/logout",methods=["GET", "POST"])(
            self.controller.logout
        )
        self.bp.route("/merchant_dashboard", methods=["GET", "POST"])(
            merchant_required(self.controller.merchant_dashboard)
        )
        self.bp.route("/shop", methods=["GET", "POST"])(
            self.shop_controller.shop
        )
        self.bp.route("/herb_library", methods=["GET"])(
            self.shop_controller.herb_library
        )
        self.bp.route("/herb_details/<int:id>", methods=["GET"])(
            self.shop_controller.herb_details
        )
        self.bp.route("/add_product", methods=["POST"])(
            merchant_required(self.shop_controller.add_product)
        )
        return self.bp