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
            # Flattened SQL query to prevent formatting/placeholder issues
            sql = "SELECT id, common_name, scientific_name, description, benefit_category, price, image_url, stock_quantity, whatsapp_number FROM herbs WHERE 1=1"
            query_args = []
            
            if query_param:
                sql += " AND (common_name LIKE %s OR scientific_name LIKE %s)"
                search_term = f"%{query_param}%"
                query_args.extend([search_term, search_term])
                
            if benefit_param:
                sql += " AND LOWER(benefit_category) = LOWER(%s)"
                query_args.append(benefit_param)
            
            # Ensure query_args is passed as a tuple
            raw_results = db.fetch_all(sql, tuple(query_args))
            db.close()
            
            formatted_herbs = []
            if raw_results:
                for row in raw_results:
                    # Adjust index mapping if your Database class returns dictionaries instead of tuples
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
        
        # Base SQL query
        query = "SELECT * FROM herbs WHERE 1=1"
        params = []
        
        # Append search condition if present
        if search_query:
            query += " AND (common_name LIKE %s OR scientific_name LIKE %s)"
            search_term = f"%{search_query}%"
            params.extend([search_term, search_term])
            
        # Append filter condition if present
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
            
        # Fetch reviews for this herb
        reviews_query = """
            SELECT r.*, u.name as user_name 
            FROM reviews r 
            JOIN users u ON r.user_id = u.id 
            WHERE r.herb_id = %s 
            ORDER BY r.created_at DESC
        """
        reviews = db.fetch_all(reviews_query, (id,))
        db.close()
        
        # Calculate review statistics
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

        # Handle optional review image upload
        image_url = None
        review_image = request.files.get("review_image")
        if review_image and review_image.filename:
            upload_dir = 'app/static/uploads'
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            ext = os.path.splitext(review_image.filename)[1]
            unique_filename = f"review_{uuid.uuid4().hex}{ext}"
            save_path = os.path.join(upload_dir, unique_filename)
            review_image.save(save_path)
            image_url = f'/static/uploads/{unique_filename}'

        # Save to database
        db = Database()
        query = """
            INSERT INTO reviews (herb_id, user_id, rating, comment, image_url, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """
        try:
            db.execute(query, (herb_id, session.get("user_id"), rating, comment, image_url))
            flash("Your review has been submitted successfully!", "success")
        except Exception as e:
            print(f"Error saving review: {e}")
            flash("An error occurred while saving your review.", "danger")
        finally:
            db.close()

        return redirect(url_for("shop.herb_details", id=herb_id))

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
            
            product_image = request.files.get('product_image')
            image_url = '/static/uploads/default_herb.png' 
            
            if product_image and product_image.filename:
                upload_dir = 'app/static/uploads'
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                    
                ext = os.path.splitext(product_image.filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                save_path = os.path.join(upload_dir, unique_filename)
                product_image.save(save_path)
                image_url = f'/static/uploads/{unique_filename}'

            try:
                db = Database()
                query = """INSERT INTO herbs 
                        (common_name, scientific_name, description, price, benefit_category, stock_quantity, image_url, merchant_id, whatsapp_number) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                
                db.execute(query, (
                    common_name, scientific_name, description, price, 
                    benefit_category, stock_quantity, image_url, session.get("user_id"), whatsapp_number
                ))
                
                # Fetch the ID of the new herb to seed the price history
                new_herb = db.fetch_one("SELECT id FROM herbs WHERE scientific_name = %s", (scientific_name,))
                if new_herb:
                    db.execute(
                        "INSERT INTO price_history (herb_id, price) VALUES (%s, %s)",
                        (new_herb["id"], price)
                    )
                
                db.close()
                flash("Product published successfully!", "success")
            except Exception as e:
                print(f"DEBUG ERROR: {e}")
                flash("Error saving product. Please check your inputs.", "danger")
                
            return redirect(url_for("auth.merchant_dashboard"))

    def update_product(self, id):
        """Secure multi-part form portal for updating a product's price and stock."""
        if session.get("role") != "merchant":
            flash("Unauthorized entry context.", "danger")
            return redirect(url_for("auth.login"))
            
        if request.method == "POST":
            price = request.form.get("price")
            stock_quantity = request.form.get("stock_quantity")
            
            if not price or stock_quantity is None:
                flash("Price and Stock Quantity are required.", "danger")
                return redirect(url_for("auth.merchant_dashboard"))
                
            try:
                price = float(price)
                stock_quantity = int(stock_quantity)
                
                db = Database()
                # Fetch current herb details to see if price changed
                herb = db.fetch_one("SELECT price, merchant_id FROM herbs WHERE id = %s", (id,))
                if not herb or herb["merchant_id"] != session.get("user_id"):
                    flash("Unauthorized or product not found.", "danger")
                    db.close()
                    return redirect(url_for("auth.merchant_dashboard"))
                    
                # Update stock and price
                db.execute(
                    "UPDATE herbs SET price = %s, stock_quantity = %s WHERE id = %s",
                    (price, stock_quantity, id)
                )
                
                # If price changed, log in history
                if float(herb["price"]) != price:
                     db.execute(
                         "INSERT INTO price_history (herb_id, price) VALUES (%s, %s)",
                         (id, price)
                     )
                     
                db.close()
                flash("Product updated successfully!", "success")
            except Exception as e:
                print(f"Error updating product: {e}")
                flash("Failed to update product.", "danger")
                
            return redirect(url_for("auth.merchant_dashboard"))

    def api_price_history(self, herb_id):
        """Fetch the price history of a product for the chart."""
        if session.get("role") != "merchant":
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
            
        db = Database()
        # Check if product belongs to merchant
        herb = db.fetch_one("SELECT merchant_id, price FROM herbs WHERE id = %s", (herb_id,))
        if not herb or herb["merchant_id"] != session.get("user_id"):
            db.close()
            return jsonify({"status": "error", "message": "Unauthorized"}), 403
            
        # Fetch history
        history = db.fetch_all("SELECT price, created_at FROM price_history WHERE herb_id = %s ORDER BY created_at ASC", (herb_id,))
        
        # If history is empty, seed it with the current price of the herb
        if not history:
            db.execute("INSERT INTO price_history (herb_id, price) VALUES (%s, %s)", (herb_id, herb["price"]))
            history = db.fetch_all("SELECT price, created_at FROM price_history WHERE herb_id = %s ORDER BY created_at ASC", (herb_id,))
            
        db.close()
        
        # Format history for JSON response
        formatted_history = []
        for record in history:
            date_str = record["created_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(record["created_at"], datetime) else str(record["created_at"])
            formatted_history.append({
                "price": float(record["price"]),
                "date": date_str
            })
            
        return jsonify({
            "status": "success",
            "history": formatted_history
        })

    # ────────────────────────────────────────────────────────────────
    #  SHOPPING CART TRANSACTION MODULES (RESILIENT TYPE-MATCHING)
    # ────────────────────────────────────────────────────────────────

    def view_cart(self):
        """Renders the transactional checkout cart template page."""
        cart_items = session.get('cart', [])
        return render_template('cart.html', items=cart_items)

    def add_to_cart(self):
        """Asynchronously appends an organic item to the session array."""
        if request.method != "POST":
            return jsonify({"status": "error", "message": "POST method expected"}), 405
            
        data = request.get_json() or {}
        herb_id = data.get('herb_id')
        
        if not herb_id:
            return jsonify({"status": "error", "message": "Missing product identifier"}), 400
            
        db = Database()
        # Added merchant_id to the SELECT query
        herb = db.fetch_one("SELECT id, common_name, scientific_name, price, image_url, merchant_id FROM herbs WHERE id = %s", (herb_id,))
        db.close()
        
        if not herb:
            return jsonify({"status": "error", "message": "Product record untraceable"}), 442

        # Map merchant_id along with other fields
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
        
        # Compare IDs safely as plain strings
        existing_item = next((item for item in cart if str(item['id']) == str(herb_mapped['id'])), None)
        
        if existing_item:
            existing_item['quantity'] += 1
        else:
            # Append merchant_id to the cart item dictionary
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
        """Adjusts values for + / - increment updates seamlessly."""
        data = request.get_json() or {}
        herb_id = data.get('herb_id')
        action = data.get('action') 
        
        if not herb_id or 'cart' not in session:
            return jsonify({"status": "error", "message": "Session target missing"}), 400
            
        cart = session['cart']
        # Standardized tracking keys to safe string types
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
        """Completely purges target item index cleanly from session."""
        data = request.get_json() or {}
        herb_id = data.get('herb_id')
        
        if not herb_id or 'cart' not in session:
            return jsonify({"status": "error", "message": "Target context missing"}), 400
            
        cart = session['cart']
        # Standardized matching comparison logic safely
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
        """Step 1: Render the checkout payment page via GET."""
        if 'cart' not in session or not session['cart']:
            flash("Your basket is empty.", "warning")
            return redirect(url_for('shop.shop'))
            
        # Grab the delivery window from URL query string and save to session
        delivery_window = request.args.get('window', '')
        session['selected_delivery_window'] = delivery_window
        
        # Calculate subtotal/total securely from the list session
        cart_total = 0.0
        for item in session.get('cart', []):
            cart_total += float(item.get('price', 0)) * int(item.get('quantity', 1))
            
        return render_template('checkout.html', delivery_window=delivery_window, cart_total=cart_total)

    def process_checkout(self):
        if 'cart' not in session or not session['cart']:
            flash("Your session expired or your basket is empty.", "warning")
            return redirect(url_for('shop.shop'))
            
        # Securely recalculate the total from the list session
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
            # Added delivery_date and CURDATE() to the insert query
            order_query = """
                INSERT INTO orders (user_id, merchant_id, total_amount, shipping_address, delivery_date, delivery_window, order_status, created_at)
                VALUES (%s, %s, %s, %s, CURDATE(), %s, 'Pending', NOW())
            """
            db.execute(order_query, (user_id, merchant_id, cart_total, shipping_address, delivery_window))
            
            order_id_cursor = db.fetch_one("SELECT LAST_INSERT_ID()") 
            order_id = order_id_cursor[0] if order_id_cursor else None
            
            if order_id:
                item_query = """
                    INSERT INTO order_items (order_id, herb_id, quantity, price_at_purchase)
                    VALUES (%s, %s, %s, %s)
                """
                for item in cart_items:
                    db.execute(item_query, (
                        order_id, 
                        item['id'], 
                        item['quantity'], 
                        item['price']
                    ))
            
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
        """Fetch order status and details for a customer using actual db schema."""
        if 'user_id' not in session:
            flash("Please log in to view your order status.", "warning")
            return redirect(url_for('auth.login'))
            
        db = Database()
        
        # Match schema column names: user_id, order_status
        order_query = """
            SELECT id, order_status, total_amount, shipping_address, delivery_date, delivery_window, created_at 
            FROM orders WHERE id = %s AND user_id = %s
        """
        order = db.fetch_one(order_query, (order_id, session['user_id']))
        
        if not order:
            db.close()
            flash("Order not found or access denied.", "danger")
            return redirect(url_for('shop.shop'))
            
        # Join order_items with herbs to get item details and images using schema keys
        items_query = """
            SELECT oi.id, oi.quantity, oi.price_at_purchase, h.common_name, h.scientific_name, h.image_url
            FROM order_items oi
            JOIN herbs h ON oi.herb_id = h.id
            WHERE oi.order_id = %s
        """
        order_items = db.fetch_all(items_query, (order_id,))
        db.close()
        
        return render_template('order_status.html', order=order, items=order_items)