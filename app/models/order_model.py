from app.models.database import Database


class Order:
    def __init__(self):
        self.db = Database()

    def get_merchant_orders(self, merchant_id):
        query = "SELECT * FROM orders WHERE merchant_id = %s ORDER BY created_at DESC"
        return self.db.fetch_all(query, (merchant_id,))

    def update_status(self, order_id, new_status, merchant_id):
        """
        Update order status, but only if the order belongs to this merchant.
        This ensures a merchant can only update their own orders.
        """
        query = """
            UPDATE orders 
            SET order_status = %s 
            WHERE id = %s AND merchant_id = %s
        """
        rows_affected = self.db.execute(
            query, (new_status, order_id, merchant_id))
        return rows_affected > 0  # Returns True only if an order was actually updated
