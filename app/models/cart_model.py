from app.models.database import Database


class CartModel:
    def get_cart_items(self, user_id):
        db = Database()
        query = """
            SELECT 
                ci.id,
                ci.user_id,
                ci.herb_id,
                ci.quantity,
                h.common_name,
                h.scientific_name,
                h.price,
                h.stock_quantity,
                h.image_url,
                (ci.quantity * h.price) AS subtotal
            FROM cart_items ci
            INNER JOIN herbs h ON ci.herb_id = h.id
            WHERE ci.user_id = %s
            ORDER BY ci.id DESC
        """
        items = db.fetch_all(query, (user_id,))
        db.close()
        return items

    def get_cart_item(self, user_id, herb_id):
        db = Database()
        query = """
            SELECT * FROM cart_items
            WHERE user_id = %s AND herb_id = %s
        """
        item = db.fetch_one(query, (user_id, herb_id))
        db.close()
        return item

    def add_to_cart(self, user_id, herb_id, quantity=1):
        db = Database()

        existing_item = db.fetch_one(
            "SELECT * FROM cart_items WHERE user_id = %s AND herb_id = %s",
            (user_id, herb_id)
        )

        herb = db.fetch_one(
            "SELECT id, stock_quantity FROM herbs WHERE id = %s",
            (herb_id,)
        )

        if not herb:
            db.close()
            return {"success": False, "message": "Product not found."}

        if herb["stock_quantity"] < quantity:
            db.close()
            return {"success": False, "message": "Not enough stock available."}

        if existing_item:
            new_quantity = existing_item["quantity"] + quantity

            if new_quantity > herb["stock_quantity"]:
                db.close()
                return {"success": False, "message": "Requested quantity exceeds available stock."}

            db.execute(
                "UPDATE cart_items SET quantity = %s WHERE user_id = %s AND herb_id = %s",
                (new_quantity, user_id, herb_id)
            )
        else:
            db.execute(
                "INSERT INTO cart_items (user_id, herb_id, quantity) VALUES (%s, %s, %s)",
                (user_id, herb_id, quantity)
            )

        db.close()
        return {"success": True, "message": "Item added to cart successfully."}

    def update_cart_item(self, item_id, user_id, quantity):
        db = Database()

        item = db.fetch_one("""
            SELECT ci.*, h.stock_quantity
            FROM cart_items ci
            INNER JOIN herbs h ON ci.herb_id = h.id
            WHERE ci.id = %s AND ci.user_id = %s
        """, (item_id, user_id))

        if not item:
            db.close()
            return {"success": False, "message": "Cart item not found."}

        if quantity <= 0:
            db.execute(
                "DELETE FROM cart_items WHERE id = %s AND user_id = %s",
                (item_id, user_id)
            )
            db.close()
            return {"success": True, "message": "Item removed from cart."}

        if quantity > item["stock_quantity"]:
            db.close()
            return {"success": False, "message": "Quantity exceeds available stock."}

        db.execute(
            "UPDATE cart_items SET quantity = %s WHERE id = %s AND user_id = %s",
            (quantity, item_id, user_id)
        )
        db.close()
        return {"success": True, "message": "Cart updated successfully."}

    def remove_cart_item(self, item_id, user_id):
        db = Database()
        item = db.fetch_one(
            "SELECT * FROM cart_items WHERE id = %s AND user_id = %s",
            (item_id, user_id)
        )

        if not item:
            db.close()
            return {"success": False, "message": "Cart item not found."}

        db.execute(
            "DELETE FROM cart_items WHERE id = %s AND user_id = %s",
            (item_id, user_id)
        )
        db.close()
        return {"success": True, "message": "Item removed from cart."}

    def get_cart_count(self, user_id):
        db = Database()
        result = db.fetch_one(
            "SELECT COALESCE(SUM(quantity), 0) AS total_items FROM cart_items WHERE user_id = %s",
            (user_id,)
        )
        db.close()
        return result["total_items"] if result else 0

    def get_cart_total(self, user_id):
        db = Database()
        result = db.fetch_one("""
            SELECT COALESCE(SUM(ci.quantity * h.price), 0) AS total_amount
            FROM cart_items ci
            INNER JOIN herbs h ON ci.herb_id = h.id
            WHERE ci.user_id = %s
        """, (user_id,))
        db.close()
        return result["total_amount"] if result else 0
