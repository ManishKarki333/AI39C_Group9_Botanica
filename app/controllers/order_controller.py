from flask import request, redirect, url_for, flash, session
from app.controllers.base_controller import BaseController
from app.models.order_model import Order
from app.auth import merchant_required
import logging


class OrderController(BaseController):
    def __init__(self):
        super().__init__()
        self.order_model = Order()

    @merchant_required
    def update_status(self, order_id):
        new_status = request.form.get("status")
        valid_statuses = ['Pending', 'Processing',
                          'Shipped', 'Delivered', 'Cancelled']

        if not new_status or new_status not in valid_statuses:
            flash("Invalid status selection.", "danger")
            return redirect(url_for("auth.merchant_dashboard"))

        try:
            # Pass the logged-in user's ID to ensure they only edit THEIR orders
            merchant_id = session.get("user_id")
            success = self.order_model.update_status(
                order_id, new_status, merchant_id)

            if success:
                flash(f"Order #{order_id} updated to {new_status}.", "success")
            else:
                # The model should return False if the order doesn't exist OR doesn't belong to this merchant
                flash("Unauthorized access or order not found.", "danger")

        except Exception as e:
            logging.error(f"Error updating order {order_id}: {e}")
            flash("A system error occurred.", "danger")

        return redirect(url_for("auth.merchant_dashboard"))
