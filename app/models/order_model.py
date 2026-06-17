from app.models.database import Database



class Order:
    def get_merchant_orders(self, merchant_id):
        db = Database()
        try:
            query = """
                SELECT o.*, u.name as customer_name, u.email as customer_email 
                FROM orders o
                JOIN users u ON o.user_id = u.id
                WHERE o.merchant_id = %s 
                ORDER BY o.created_at DESC
            """
            return db.fetch_all(query, (merchant_id,))
        finally:
            db.close()

    def update_status(self, order_id, new_status, merchant_id):
        """
        Update order status, but only if the order belongs to this merchant.
        This ensures a merchant can only update their own orders.
        """
        db = Database()
        try:
            query = """
                UPDATE orders 
                SET order_status = %s 
                WHERE id = %s AND merchant_id = %s
            """
            rows_affected = db.execute(
                query, (new_status, order_id, merchant_id))
            print(f"--- DEBUG UPDATE ---")
            print(f"Order ID: {order_id} (Type: {type(order_id)})")
            print(f"New Status: {new_status}")
            print(f"Merchant ID: {merchant_id} (Type: {type(merchant_id)})")
            print(f"Rows Impacted: {rows_affected}")
            print(f"--------------------")
            return rows_affected > 0  # Returns True only if an order was actually updated
        finally:
            db.close()

