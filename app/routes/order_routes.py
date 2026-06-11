<<<<<<< HEAD
# from flask import Blueprint
# from app.controllers.order import OrderController

# class OrderRoutes:
#     def __init__(self):
#         self.bp = Blueprint("order", __name__)
#         self.controller = OrderController()

#     def register(self):
#         self.bp.add_url_rule(
#             "/order_status",
#             endpoint="order_status",
#             view_func=self.controller.order_status,
#             methods=["GET"]
#         )
#         return self.bp
=======
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
>>>>>>> ffbbe146b7b51e9e67d18c219562ea8c3f8932ae
