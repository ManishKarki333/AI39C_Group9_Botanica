from flask import Blueprint
from app.controllers.order_controller import OrderController
from app.auth import merchant_required

class OrderRoutes:
    def __init__(self):
        self.bp = Blueprint("order", __name__)
        self.controller = OrderController()

    def register(self):
        self.bp.route('/update/<int:order_id>', methods=['POST'])(
            merchant_required(self.controller.update_status)
        )
        return self.bp
