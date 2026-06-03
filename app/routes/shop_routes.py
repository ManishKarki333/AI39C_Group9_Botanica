from flask import Blueprint
from app.controllers.shop_controller import ShopController
from app.controllers.auth import AuthController
from app.auth import merchant_required 

class ShopRoutes:
    def __init__(self):
        # Instantiates a clean, independent sub-module for e-commerce logic
        self.bp = Blueprint("shop", __name__)
        self.shop_controller = ShopController()
        self.auth_controller = AuthController() # Used for cart templates if needed

    def register(self):
        self.bp.route("/shop", methods=["GET", "POST"])(
            self.shop_controller.shop
        )
        self.bp.route("/herb_library", methods=["GET"])(
            self.shop_controller.herb_library
        )
        self.bp.route("/herb_details/<int:id>", methods=["GET"])(
            self.shop_controller.herb_details
        )
        
        # Protected inventory management mutations
        self.bp.route("/add_product", methods=["POST"])(
            merchant_required(self.shop_controller.add_product)
        )
        
        # Handing over cart mapping clean to the e-commerce engine namespace
        self.bp.route("/cart", methods=["GET", "POST"])(
            self.auth_controller.cart
        )
        
        return self.bp