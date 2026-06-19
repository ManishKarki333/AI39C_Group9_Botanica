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
        

