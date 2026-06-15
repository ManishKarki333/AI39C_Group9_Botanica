import uuid
import os
from flask import render_template, request, session, redirect, url_for, flash, jsonify
from app.controllers.base_controller import BaseController
from app.models.database import Database
from datetime import datetime


class ShopController(BaseController):

    def shop(self):
        """Handle the main synchronous marketplace grid view."""
        db = Database()
        search_query = request.args.get('search', '').strip()
        category_filter = request.args.get('category', '').strip()

        query = "SELECT * FROM herbs WHERE 1=1"
        params = []

        if search_query:
            query += " AND (common_name LIKE %s OR scientific_name LIKE %s)"
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param])

        if category_filter:
            query += " AND benefit_category = %s"
            params.append(category_filter)

        herbs_list = db.fetch_all(query, tuple(params))
        db.close()
        return render_template('shop.html', herbs=herbs_list, search=search_query, current_category=category_filter)

    def api_search_and_filter(self):
        query_param = request.args.get('q', '').strip()
        benefit_param = request.args.get('benefit', '').strip()

        print(f"DEBUG: query_param='{query_param}', benefit_param='{benefit_param}'")

        try:
            db = Database()
            sql = "SELECT id, common_name, scientific_name, description, benefit_category, price, image_url, stock_quantity, whatsapp_number FROM herbs WHERE 1=1"
            query_args = []

            if query_param:
                sql += " AND (common_name LIKE %s OR scientific_name LIKE %s)"
                search_term = f"%{query_param}%"
                query_args.extend([search_term, search_term])

            if benefit_param:
                sql += " AND LOWER(benefit_category) = LOWER(%s)"
                query_args.append(benefit_param)

            raw_results = db.fetch_all(sql, tuple(query_args))
            db.close()

            formatted_herbs = []
            if raw_results:
                for row in raw_results:
                    formatted_herbs.append({
                        "id": row.get('id'),
                        "common_name": row.get('common_name'),
                        "scientific_name": row.get('scientific_name'),
                        "description": row.get('description'),
                        "benefit_category": row.get('benefit_category'),
                        "price": float(row['price']) if row.get('price') else 0.0,
                        "image_url": row.get('image_url') if row.get('image_url') else "",
                        "form_factor": "Raw Herb",
                        "on_vacation": False,
                        "stock_quantity": row.get('stock_quantity', 0),
                        "whatsapp_number": row.get('whatsapp_number') or ""
                    })

            return jsonify({
                "status": "success",
                "count": len(formatted_herbs),
                "data": formatted_herbs
            }), 200

        except Exception as e:
            print(f"CRITICAL BACKEND ERROR DETAILED: {repr(e)}")
            return jsonify({
                "status": "error",
                "message": f"Async engine failed: {str(e)}"
            }), 500

    def herb_library(self):
        """Fetch all herbs, or filter/search them for the reference library module."""
        db = Database()
        search_query = request.args.get('search', '').strip()
        filter_benefit = request.args.get('filter', '').strip()

        query = "SELECT * FROM herbs WHERE 1=1"
        params = []

        if search_query:
            query += " AND (common_name LIKE %s OR scientific_name LIKE %s)"
            search_term = f"%{search_query}%"
            params.extend([search_term, search_term])

        if filter_benefit:
            query += " AND benefit_category LIKE %s"
            filter_term = f"%{filter_benefit}%"
            params.append(filter_term)

        herbs = db.fetch_all(query, tuple(params))
        db.close()

        return render_template(
            "herb_library.html",
            herbs=herbs,
            search_query=search_query,
            filter_benefit=filter_benefit
        )

    def herb_details(self, id):
        db = Database()
        herb = db.fetch_one("SELECT * FROM herbs WHERE id = %s", (id,))

        if not herb:
            db.close()
            flash("Herb record not found.", "danger")
            return redirect(url_for("shop.shop"))

        reviews_query = """
            SELECT r.*, u.name as user_name 
            FROM reviews r 
            JOIN users u ON r.user_id = u.id 
            WHERE r.herb_id = %s 
            ORDER BY r.created_at DESC
        """
        reviews = db.fetch_all(reviews_query, (id,))
        db.close()

        total_reviews = len(reviews)
        average_rating = 0.0
        if total_reviews > 0:
            average_rating = sum(r['rating'] for r in reviews) / total_reviews
            average_rating = round(average_rating, 1)

        return render_template(
            "herb_details.html",
            herb=herb,
            reviews=reviews,
            average_rating=average_rating,
            total_reviews=total_reviews
        )

    def add_review(self, herb_id):
        if 'user_id' not in session:
            flash("Please log in to leave a review.", "danger")
            return redirect(url_for("auth.login"))

        rating = request.form.get("rating")
        comment = request.form.get("comment", "").strip()

        if not rating or not comment:
            flash("Rating and comment are required.", "danger")
            return redirect(url_for("shop.herb_details", id=herb_id))

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError()
        except ValueError:
            flash("Invalid rating selected.", "danger")
            return redirect(url_for("shop.herb_details", id=herb_id))

        image_url = None
        review_image = request.files.get("review_image")
        if review_image and review_image.filename:
            upload_dir = 'app/static/uploads'
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            ext = os.path.splitext(review_image.filename)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                unique_filename = f"review_{uuid.uuid4().hex}{ext}"
                save_path = os.path.join(upload_dir, unique_filename)
                review_image.save(save_path)
                image_url = f'/static/uploads/{unique_filename}'

        db = Database()
        query = """
            INSERT INTO reviews (herb_id, user_id, rating, comment, image_url, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        try:
            db.execute(query, (herb_id, session.get("user_id"), rating, comment, image_url))
            if hasattr(db, 'commit'): db.commit()
            flash("Your review has been submitted successfully!", "success")
        except Exception as e:
            print(f"Error saving review: {e}")
            flash("An error occurred while saving your review.", "danger")
        finally:
            db.close()

        return redirect(url_for("shop.herb_details", id=herb_id))

    def delete_review(self, review_id):
        """Secure portal endpoint allowing authors or admins to drop reviews."""
        if 'user_id' not in session:
            flash("Please log in to manage your content.", "danger")
            return redirect(url_for("auth.login"))

        user_id = session.get("user_id")
        user_role = session.get("role")

        db = Database()
        try:
            review = db.fetch_one("SELECT id, user_id, herb_id, image_url FROM reviews WHERE id = %s", (review_id,))
            
            if not review:
                flash("Review record untraceable.", "danger")
                return redirect(url_for("shop.shop"))
                
            herb_id = review.get('herb_id')

            if review.get('user_id') != user_id and user_role != "admin":
                flash("Unauthorized deletion context requested.", "danger")
                return redirect(url_for("shop.herb_details", id=herb_id))

            if review.get('image_url'):
                relative_path = review['image_url'].lstrip('/')
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                absolute_image_path = os.path.join(base_dir, relative_path)
                if os.path.exists(absolute_image_path):
                    os.remove(absolute_image_path)

            db.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
            if hasattr(db, 'commit'): db.commit()
            flash("Your review has been removed successfully.", "success")
            return redirect(url_for("shop.herb_details", id=herb_id))

        except Exception as e:
            print(f"Error executing review drop process: {e}")
            flash("System failed to complete review deletion.", "danger")
            return redirect(url_for("shop.shop"))
        finally:
            db.close()

    def add_product(self):
        """Secure multi-part form portal for inventory deployment."""
        if session.get("role") != "merchant":
            flash("Unauthorized entry context.", "danger")
            return redirect(url_for("auth.login"))

        if request.method == "POST":
            common_name = request.form.get("common_name", "").strip()
            scientific_name = request.form.get("scientific_name", "").strip()
            description = request.form.get("description", "").strip()
            price = request.form.get("price", 0)
            benefit_category = request.form.get("benefit_category", "")
            stock_quantity = request.form.get("stock_quantity", 0)
            whatsapp_number = request.form.get("whatsapp_number", "").strip()
            reference_url = request.form.get("reference_url", "").strip()

            product_image = request.files.get('product_image')
            image_url = '/static/uploads/default_herb.png'

            if product_image and product_image.filename:
                upload_dir = 'app/static/uploads'
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)

                ext = os.path.splitext(product_image.filename)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                    unique_filename = f"{uuid.uuid4().hex}{ext}"
                    save_path = os.path.join(upload_dir, unique_filename)
                    product_image.save(save_path)
                    image_url = f'/static/uploads/{unique_filename}'

            try:
                db = Database()
                query = """INSERT INTO herbs 
                        (common_name, scientific_name, description, price, benefit_category, stock_quantity, image_url, merchant_id, whatsapp_number, reference_url) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                db.execute(query, (
                    common_name, scientific_name, description, price,
                    benefit_category, stock_quantity, image_url, session.get("user_id"), whatsapp_number, reference_url
                ))
                if hasattr(db, 'commit'): db.commit()

                new_herb = db.fetch_one("SELECT id FROM herbs WHERE scientific_name = %s", (scientific_name,))
                if new_herb:
                    db.execute(
                        "INSERT INTO price_history (herb_id, price) VALUES (%s, %s)",
                        (new_herb["id"], price)
                    )
                    if hasattr(db, 'commit'): db.commit()

                db.close()
                flash("Product published successfully!", "success")
            except Exception as e:
                print(f"DEBUG ERROR: {e}")
                flash("Error saving product. Please check your inputs.", "danger")

            return redirect(url_for("auth.merchant_dashboard"))

    def update_product(self, id):
        """Secure multi-part form portal for updating a product's details and price/stock."""
        if session.get("role") != "merchant":
            flash("Unauthorized entry context.", "danger")
            return redirect(url_for("auth.login"))

        if request.method == "POST":
            common_name = request.form.get("common_name", "").strip()
            scientific_name = request.form.get("scientific_name", "").strip()
            price = request.form.get("price")
            stock_quantity = request.form.get("stock_quantity")
            whatsapp_number = request.form.get("whatsapp_number", "").strip()
            reference_url = request.form.get("reference_url", "").strip()

            if not common_name or not scientific_name or not price or stock_quantity is None:
                flash("Name, Scientific Name, Price, and Stock Quantity are required.", "danger")
                return redirect(url_for("auth.merchant_dashboard"))

            try:
                price = float(price)
                stock_quantity = int(stock_quantity)

                db = Database()
                herb = db.fetch_one("SELECT price, merchant_id FROM herbs WHERE id = %s", (id,))
                if not herb or herb["merchant_id"] != session.get("user_id"):
                    flash("Unauthorized or product not found.", "danger")
                    db.close()
                    return redirect(url_for("auth.merchant_dashboard"))

                db.execute(
                    "UPDATE herbs SET common_name = %s, scientific_name = %s, price = %s, stock_quantity = %s, whatsapp_number = %s, reference_url = %s WHERE id = %s",
                    (common_name, scientific_name, price, stock_quantity, whatsapp_number, reference_url, id)
                )
                if hasattr(db, 'commit'): db.commit()

                if float(herb["price"]) != price:
                    db.execute(
                        "INSERT INTO price_history (herb_id, price) VALUES (%s, %s)",
                        (id, price)
                    )
                    if hasattr(db, 'commit'): db.commit()

                db.close()
                flash("Product updated successfully!", "success")
            except Exception as e:
                print(f"Error updating product: {e}")
                if "Duplicate entry" in str(e) or "1062" in str(e):
                    flash("Failed to update product: The scientific name is already in use by another herb.", "danger")
                else:
                    flash("Failed to update product.", "danger")

            return redirect(url_for("auth.merchant_dashboard"))

    def delete_product(self, id):
        """Secure endpoint for deleting a product from inventory."""
        if session.get("role") != "merchant":
            flash("Unauthorized entry context.", "danger")
            return redirect(url_for("auth.login"))

        db = Database()
        try:
            # Check if product belongs to merchant
            herb = db.fetch_one("SELECT merchant_id, image_url, common_name FROM herbs WHERE id = %s", (id,))
            if not herb or herb["merchant_id"] != session.get("user_id"):
                flash("Product not found or unauthorized.", "danger")
                db.close()
                return redirect(url_for("auth.merchant_dashboard"))

            # Delete the product image if it's not the default image
            if herb.get("image_url") and herb["image_url"] != '/static/uploads/default_herb.png':
                relative_path = herb["image_url"].lstrip('/')
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                absolute_image_path = os.path.join(base_dir, relative_path)
                if os.path.exists(absolute_image_path):
                    try:
                        os.remove(absolute_image_path)
                    except Exception as img_err:
                        print(f"Error removing product image file: {img_err}")

            # Delete from database
            db.execute("DELETE FROM herbs WHERE id = %s", (id,))
            if hasattr(db, 'commit'): db.commit()
            
            flash(f"Product '{herb['common_name']}' deleted successfully.", "success")
        except Exception as e:
            print(f"Error deleting product: {e}")
            flash("Failed to delete product.", "danger")
        finally:
            db.close()

        return redirect(url_for("auth.merchant_dashboard"))

    def herb_detail_library(self, id):
        """Fetch details of a herb specifically for the academic reference library view."""
        db = Database()
        herb = db.fetch_one("SELECT * FROM herbs WHERE id = %s", (id,))

        if not herb:
            db.close()
            flash("Herb record not found.", "danger")
            return redirect(url_for("shop.herb_library"))

        reviews_query = """
            SELECT r.*, u.name as user_name 
            FROM reviews r 
            JOIN users u ON r.user_id = u.id 
            WHERE r.herb_id = %s 
            ORDER BY r.created_at DESC
        """
        reviews = db.fetch_all(reviews_query, (id,))
        db.close()

        total_reviews = len(reviews)
        average_rating = 0.0
        if total_reviews > 0:
            average_rating = sum(r['rating'] for r in reviews) / total_reviews
            average_rating = round(average_rating, 1)

        return render_template(
            "herb_detail_library.html",
            herb=herb,
            reviews=reviews,
            average_rating=average_rating,
            total_reviews=total_reviews
        )

    def api_price_history(self, herb_id):
        if session.get("role") != "merchant":
            return jsonify({"status": "error", "message": "Unauthorized"}), 403

        db = Database()
        herb = db.fetch_one("SELECT merchant_id, price FROM herbs WHERE id = %s", (herb_id,))
        if not herb or herb["merchant_id"] != session.get("user_id"):
            db.close()
            return jsonify({"status": "error", "message": "Unauthorized"}), 403

        history = db.fetch_all("SELECT price, created_at FROM price_history WHERE herb_id = %s ORDER BY created_at ASC", (herb_id,))

        if not history:
            db.execute("INSERT INTO price_history (herb_id, price) VALUES (%s, %s)", (herb_id, herb["price"]))
            if hasattr(db, 'commit'): db.commit()
            history = db.fetch_all("SELECT price, created_at FROM price_history WHERE herb_id = %s ORDER BY created_at ASC", (herb_id,))

        db.close()

        formatted_history = []
        for record in history:
            date_str = record["created_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(
                record["created_at"], datetime) else str(record["created_at"])
            formatted_history.append({
                "price": float(record["price"]),
                "date": date_str
            })

        return jsonify({
            "status": "success",
            "history": formatted_history
        })

    def view_cart(self):
        cart_items = session.get('cart', [])
        return render_template('cart.html', items=cart_items)

    def add_to_cart(self):
        if request.method != "POST":
            return jsonify({"status": "error", "message": "POST method expected"}), 405

        data = request.get_json() or {}
        herb_id = data.get('herb_id')

        if not herb_id:
            return jsonify({"status": "error", "message": "Missing product identifier"}), 400

        db = Database()
        herb = db.fetch_one("SELECT id, common_name, scientific_name, price, image_url, merchant_id FROM herbs WHERE id = %s", (herb_id,))
        db.close()

        if not herb:
            return jsonify({"status": "error", "message": "Product record untraceable"}), 442

        herb_mapped = {
            "id": herb['id'],
            "common_name": herb['common_name'],
            "scientific_name": herb['scientific_name'],
            "price": float(herb['price']) if herb.get('price') else 0.0,
            "image_url": herb.get('image_url') or '/static/uploads/default_herb.png',
            "merchant_id": herb.get('merchant_id')
        }

        if 'cart' not in session:
            session['cart'] = []

        cart = session['cart']
        existing_item = next((item for item in cart if str(item['id']) == str(herb_mapped['id'])), None)

        if existing_item:
            existing_item['quantity'] += 1
        else:
            cart.append({
                'id': herb_mapped['id'],
                'common_name': herb_mapped['common_name'],
                'scientific_name': herb_mapped['scientific_name'],
                'price': herb_mapped['price'],
                'quantity': 1,
                'image_url': herb_mapped['image_url'],
                'merchant_id': herb_mapped['merchant_id']
            })

        session['cart'] = cart
        session.modified = True

        return jsonify({
            "status": "success",
            "message": f"Added {herb_mapped['common_name']} to your basket.",
            "cart_count": sum(item['quantity'] for item in session['cart'])
        }), 200

    def update_cart_quantity(self):
        data = request.get_json() or {}
        herb_id = data.get('herb_id')
        action = data.get('action')

        if not herb_id or 'cart' not in session:
            return jsonify({"status": "error", "message": "Session target missing"}), 400

        cart = session['cart']
        item = next((i for i in cart if str(i['id']) == str(herb_id)), None)

        if item:
            if action == 'increment':
                item['quantity'] += 1
            elif action == 'decrement':
                item['quantity'] -= 1
                if item['quantity'] <= 0:
                    cart = [i for i in cart if str(i['id']) != str(herb_id)]

            session['cart'] = cart
            session.modified = True

            subtotal = sum(i['price'] * i['quantity'] for i in cart)
            return jsonify({
                "status": "success",
                "cart_count": sum(i['quantity'] for i in cart),
                "subtotal": subtotal
            }), 200

        return jsonify({"status": "error", "message": "Item missing from basket context"}), 442

    def remove_from_cart(self):
        data = request.get_json() or {}
        herb_id = data.get('herb_id')

        if not herb_id or 'cart' not in session:
            return jsonify({"status": "error", "message": "Target context missing"}), 400

        cart = session['cart']
        updated_cart = [item for item in cart if str(item['id']) != str(herb_id)]

        session['cart'] = updated_cart
        session.modified = True

        subtotal = sum(i['price'] * i['quantity'] for i in updated_cart)
        return jsonify({
            "status": "success",
            "cart_count": sum(i['quantity'] for i in updated_cart),
            "subtotal": subtotal
        }), 200

    def checkout_page(self):
        if 'cart' not in session or not session['cart']:
            flash("Your basket is empty.", "warning")
            return redirect(url_for('shop.shop'))

        delivery_window = request.args.get('window', '')
        session['selected_delivery_window'] = delivery_window

        cart_total = 0.0
        for item in session.get('cart', []):
            cart_total += float(item.get('price', 0)) * int(item.get('quantity', 1))

        return render_template('checkout.html', delivery_window=delivery_window, cart_total=cart_total)

    def process_checkout(self):
        if 'cart' not in session or not session['cart']:
            flash("Your session expired or your basket is empty.", "warning")
            return redirect(url_for('shop.shop'))

        cart_total = 0.0
        for item in session.get('cart', []):
            cart_total += float(item.get('price', 0)) * int(item.get('quantity', 1))

        delivery_window = session.get('selected_delivery_window', '')
        user_id = session.get('user_id')
        shipping_address = request.form.get('shipping_address', '').strip()

        cart_items = session.get('cart', [])
        merchant_id = cart_items[0].get('merchant_id') if cart_items else None

        if not user_id:
            flash("You must be logged in to place an order.", "danger")
            return redirect(url_for('auth.login'))

        if not merchant_id:
            flash("Cannot determine the merchant for this order.", "danger")
            return redirect(url_for('shop.view_cart'))

        db = Database()
        try:
            order_query = """
                INSERT INTO orders (user_id, merchant_id, total_amount, shipping_address, delivery_date, delivery_window, order_status, created_at)
                VALUES (%s, %s, %s, %s, CURDATE(), %s, 'Pending', NOW())
            """
            db.execute(order_query, (user_id, merchant_id, cart_total, shipping_address, delivery_window))
            if hasattr(db, 'commit'): db.commit()

            order_id_cursor = db.fetch_one("SELECT LAST_INSERT_ID()")
            order_id = order_id_cursor.get('LAST_INSERT_ID()') if order_id_cursor else None

            if order_id:
                item_query = """
                    INSERT INTO order_items (order_id, herb_id, quantity, price_at_purchase)
                    VALUES (%s, %s, %s, %s)
                """
                for item in cart_items:
                    db.execute(item_query, (order_id, item['id'], item['quantity'], item['price']))
                if hasattr(db, 'commit'): db.commit()

            session.pop('cart', None)
            session.pop('selected_delivery_window', None)

            flash("Order placed successfully!", "success")
            return redirect(url_for('auth.profile'))

        except Exception as e:
            print("Database Insert Error:", e)
            flash("An error occurred while processing your order. Please try again.", "danger")
            return redirect(url_for('shop.view_cart'))
        finally:
            db.close()

    def track_order_status(self, order_id):
        if 'user_id' not in session:
            flash("Please log in to view your order status.", "warning")
            return redirect(url_for('auth.login'))

        db = Database()
        order_query = """
            SELECT id, order_status, total_amount, shipping_address, delivery_date, delivery_window, created_at 
            FROM orders WHERE id = %s AND user_id = %s
        """
        order = db.fetch_one(order_query, (order_id, session['user_id']))

        if not order:
            db.close()
            flash("Order not found or access denied.", "danger")
            return redirect(url_for('shop.shop'))

        items_query = """
            SELECT oi.id, oi.quantity, oi.price_at_purchase, h.common_name, h.scientific_name, h.image_url
            FROM order_items oi
            JOIN herbs h ON oi.herb_id = h.id
            WHERE oi.order_id = %s
        """
        order_items = db.fetch_all(items_query, (order_id,))
        db.close()

        status_steps = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']

        return render_template(
            'order_status.html', 
            order=order, 
            items=order_items, 
            status_list=status_steps
        )