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
