from app.models.database import Database

class Order:
    def __init__(self):
        self.db = Database()

    # In app/models/order_model.py
    def update_status(self, order_id, new_status, merchant_id):
        query = """
            UPDATE orders 
            SET order_status = %(status)s 
            WHERE id = %(order_id)s AND merchant_id = %(merchant_id)s
        """
        data = {
            "status": new_status,
            "order_id": order_id,
            "merchant_id": merchant_id
        }
        # execute returns the number of affected rows
        rows_affected = self.db.execute(query, data)
        return rows_affected > 0 # Returns True only if an order was actually updated
    
    def get_merchant_orders(self, merchant_id):
        query = "SELECT * FROM orders WHERE merchant_id = %s ORDER BY created_at DESC;"
        # Change 'query' to whatever your database method is actually named
        return self.db.fetch_all(query, (merchant_id,))