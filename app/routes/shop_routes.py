from flask import Blueprint
from app.controllers.shop_controller import ShopController
from app.auth import merchant_required


class ShopRoutes:
    def __init__(self):
        # Instantiates a clean, independent sub-module for e-commerce logic
        self.bp = Blueprint("shop", __name__)
        self.shop_controller = ShopController()

    def register(self):
        # Core Marketplace Views
        self.bp.route("/", methods=["GET", "POST"])(
            self.shop_controller.shop
        )
        self.bp.route("/herb_library", methods=["GET"])(
            self.shop_controller.herb_library
        )
        self.bp.route("/herb_details/<int:id>", methods=["GET"])(
            self.shop_controller.herb_details
        )

        # Protected Merchant Inventory Actions
        self.bp.route("/add_product", methods=["POST"])(
            merchant_required(self.shop_controller.add_product)
        )
        self.bp.route("/update_product/<int:id>", methods=["POST"])(
            merchant_required(self.shop_controller.update_product)
        )
        self.bp.route("/api/price_history/<int:herb_id>", methods=["GET"])(
            merchant_required(self.shop_controller.api_price_history)
        )

        # Synchronous Cart View Page
        # FIXED: Bound to shop_controller rather than auth_controller
        self.bp.route("/cart", methods=["GET"])(
            self.shop_controller.view_cart
        )

        # GET route to view the checkout form
        self.bp.route("/checkout", methods=["GET"])(
            self.shop_controller.checkout_page
        )

        # POST route triggered when the user submits their payment/checkout form
        self.bp.route("/process_checkout", methods=["POST"])(
            self.shop_controller.process_checkout
        )

        # Asynchronous API Endpoints (Sprint 3 Cart Transactions)
        self.bp.route("/add_to_cart", methods=["POST"])(
            self.shop_controller.add_to_cart
        )
        self.bp.route("/update_cart", methods=["POST"])(
            self.shop_controller.update_cart_quantity
        )
        self.bp.route("/remove_from_cart", methods=["POST"])(
            self.shop_controller.remove_from_cart
        )

        # ADD THIS: Search API for search.js
        self.bp.route("/api/search", methods=["GET"])(
            self.shop_controller.api_search_and_filter
        )

        # NEW: Order Status Tracking Endpoint
        self.bp.route("/order_status/<int:order_id>", methods=["GET"])(
            self.shop_controller.track_order_status
        )

        # NEW: Add Review Endpoint
        self.bp.route("/add_review/<int:herb_id>", methods=["POST"])(
            self.shop_controller.add_review
        )

        return self.bp
