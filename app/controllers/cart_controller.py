from flask import render_template, request, session, redirect, url_for, flash
from app.models.cart_model import CartModel


class CartController:
    def __init__(self):
        self.cart_model = CartModel()

    def view_cart(self):
        print("VIEW CART HIT")
        print("SESSION DATA:", dict(session))

        user_id = session.get("user_id")
        if not user_id:
            print("NO USER ID IN SESSION")
            flash("Please login to view your cart.", "warning")
            return redirect(url_for("auth.login"))

        try:
            cart_items = self.cart_model.get_cart_items(user_id)
            cart_total = self.cart_model.get_cart_total(user_id)

            print("CART ITEMS:", cart_items)
            print("CART TOTAL:", cart_total)

            return render_template(
                "cart.html",
                cart_items=cart_items,
                cart_total=cart_total
            )
        except Exception as e:
            print("VIEW CART ERROR:", e)
            flash(f"Cart error: {e}", "danger")
            return redirect(url_for("auth.shop"))

    def add_to_cart(self, herb_id):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please login to add items to your cart.", "warning")
            return redirect(url_for("auth.login"))

        quantity = request.form.get("quantity", 1)

        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1

        try:
            result = self.cart_model.add_to_cart(user_id, herb_id, quantity)
            print("ADD TO CART RESULT:", result)
            flash(result["message"], "success" if result["success"] else "danger")
        except Exception as e:
            print("ADD TO CART ERROR:", e)
            flash(f"Add to cart error: {e}", "danger")

        return redirect(url_for("auth.shop"))

    def update_cart(self, item_id):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))

        quantity = request.form.get("quantity", 1)

        try:
            quantity = int(quantity)
        except ValueError:
            quantity = 1

        try:
            result = self.cart_model.update_cart_item(item_id, user_id, quantity)
            print("UPDATE CART RESULT:", result)
            flash(result["message"], "success" if result["success"] else "danger")
        except Exception as e:
            print("UPDATE CART ERROR:", e)
            flash(f"Update cart error: {e}", "danger")

        return redirect(url_for("auth.view_cart"))

    def remove_from_cart(self, item_id):
        user_id = session.get("user_id")
        if not user_id:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))

        try:
            result = self.cart_model.remove_cart_item(item_id, user_id)
            print("REMOVE CART RESULT:", result)
            flash(result["message"], "success" if result["success"] else "danger")
        except Exception as e:
            print("REMOVE CART ERROR:", e)
            flash(f"Remove cart error: {e}", "danger")

        return redirect(url_for("auth.view_cart"))
