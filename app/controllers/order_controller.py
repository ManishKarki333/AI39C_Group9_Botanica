from flask import request, jsonify, session
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
        new_status = request.form.get("order_status")
        
        valid_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']

        if not new_status or new_status not in valid_statuses:
            return jsonify({"status": "error", "message": "Invalid status selection."}), 400

        try:
            merchant_id = session.get("user_id")
            success = self.order_model.update_status(order_id, new_status, merchant_id)

            if success:
                return jsonify({
                    "status": "success", 
                    "message": f"Order #{order_id} updated to {new_status}."
                }), 200
            else:
                return jsonify({"status": "error", "message": "Unauthorized access or order not found."}), 403

        except Exception as e:
            logging.error(f"Error updating order {order_id}: {e}")
            return jsonify({"status": "error", "message": "A system error occurred."}), 500

    @merchant_required
    def update_payment_status(self, order_id):
        new_payment_status = request.form.get("payment_status")
        
        valid_statuses = ['Unpaid', 'Paid']

        if not new_payment_status or new_payment_status not in valid_statuses:
            return jsonify({"status": "error", "message": "Invalid payment status selection."}), 400

        try:
            merchant_id = session.get("user_id")
            from app.models.database import Database
            db = Database()
            
            # Verify the order belongs to this merchant and get current status
            order = db.fetch_one("SELECT id, payment_status FROM orders WHERE id = %s AND merchant_id = %s", (order_id, merchant_id))
            if not order:
                db.close()
                return jsonify({"status": "error", "message": "Unauthorized access or order not found."}), 403

            # If transitioning to Paid from Unpaid/Pending
            if order.get('payment_status') != 'Paid' and new_payment_status == 'Paid':
                # Fetch order items to reduce stock
                items = db.fetch_all("SELECT herb_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
                for item in items:
                    db.execute(
                        "UPDATE herbs SET stock_quantity = GREATEST(0, stock_quantity - %s) WHERE id = %s",
                        (item['quantity'], item['herb_id'])
                    )
                    if hasattr(db, 'commit'): db.commit()

            # Update payment status
            db.execute("UPDATE orders SET payment_status = %s WHERE id = %s", (new_payment_status, order_id))
            if hasattr(db, 'commit'): db.commit()
            db.close()

            return jsonify({
                "status": "success", 
                "message": f"Order #{order_id} payment status updated to {new_payment_status}."
            }), 200

        except Exception as e:
            logging.error(f"Error updating payment status for order {order_id}: {e}")
            return jsonify({"status": "error", "message": "A system error occurred."}), 500