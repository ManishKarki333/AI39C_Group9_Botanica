import uuid
import os
from flask import render_template, request, session, redirect, url_for, flash, jsonify
from app.controllers.base_controller import BaseController
from app.models.database import Database

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
        """
        Asynchronous API Endpoint supporting live search updates.
        Maps to Sprint 1 Acceptance Criteria for live search filtering.
        """
        query_param = request.args.get('q', '').strip()
        benefit_param = request.args.get('benefit', '').strip()
        
        try:
            db = Database()
            sql = """
                SELECT id, common_name, scientific_name, description, 
                    benefit_category, price, image_url 
                FROM herbs WHERE 1=1
            """
            query_args = []
            
            if query_param:
                sql += " AND (common_name LIKE %s OR scientific_name LIKE %s)"
                search_term = f"%{query_param}%"
                query_args.extend([search_term, search_term])
                
            if benefit_param:
                sql += " AND benefit_category LIKE %s"
                benefit_term = f"%{benefit_param}%"
                query_args.append(benefit_term)
            
            raw_results = db.fetch_all(sql, tuple(query_args))
            db.close()
            
            formatted_herbs = []
            for row in raw_results:
                formatted_herbs.append({
                    "id": row[0],
                    "common_name": row[1],
                    "scientific_name": row[2],
                    "description": row[3],
                    "benefit_category": row[4],
                    "price": float(row[5]) if row[5] else 0.0,
                    "image_url": row[6] if row[6] else "",
                    "form_factor": "Raw Herb", 
                    "on_vacation": False 
                })
            
            return jsonify({
                "status": "success",
                "count": len(formatted_herbs),
                "data": formatted_herbs
            }), 200
            
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Async engine failed: {str(e)}"
            }), 500

    def herb_library(self):
        """Fetch all herbs for the reference library module."""
        db = Database()
        herbs = db.fetch_all("SELECT * FROM herbs")
        db.close()
        return render_template("herb_library.html", herbs=herbs)
    
    def herb_details(self, id):
        db = Database()
        herb = db.fetch_one("SELECT * FROM herbs WHERE id = %s", (id,))
        db.close()
        if not herb:
            flash("Herb record not found.", "danger")
            return redirect(url_for("shop.shop")) 
        return render_template("herb_details.html", herb=herb)

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
                        (common_name, scientific_name, description, price, benefit_category, stock_quantity, image_url, merchant_id) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                
                db.execute(query, (
                    common_name, scientific_name, description, price, 
                    benefit_category, stock_quantity, image_url, session.get("user_id")
                ))
                db.close()
                flash("Product published successfully!", "success")
            except Exception as e:
                print(f"DEBUG ERROR: {e}")
                flash("Error saving product. Please check your inputs.", "danger")
                
            return redirect(url_for("auth.merchant_dashboard"))

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
        herb = db.fetch_one("SELECT id, common_name, scientific_name, price, image_url FROM herbs WHERE id = %s", (herb_id,))
        db.close()
        
        if not herb:
            return jsonify({"status": "error", "message": "Product record untraceable"}), 442

        # Standardize record parsing structures cleanly
        herb_mapped = {
            "id": herb[0],
            "common_name": herb[1],
            "scientific_name": herb[2],
            "price": float(herb[3]) if herb[3] else 0.0,
            "image_url": herb[4] if herb[4] else '/static/uploads/default_herb.png'
        }

        if 'cart' not in session:
            session['cart'] = []
            
        cart = session['cart']
        
        # CRITICAL RESILIENCE FIX: Compare IDs safely as plain strings.
        # This prevents type crashes if IDs are alphanumeric, UUIDs, or numbers.
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
                'image_url': herb_mapped['image_url']
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