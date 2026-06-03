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
        # Read parameters from frontend async Fetch requests
        query_param = request.args.get('q', '').strip()
        benefit_param = request.args.get('benefit', '').strip()
        
        try:
            db = Database()
            sql = "SELECT id, common_name, scientific_name, description, benefit_category, price, image_url FROM herbs WHERE 1=1"
            query_args = []
            
            # Check text inputs case-insensitively
            if query_param:
                sql += " AND (common_name LIKE %s OR scientific_name LIKE %s)"
                search_term = f"%{query_param}%"
                query_args.extend([search_term, search_term])
                
            # Filter matches benefit_category mapping
            if benefit_param:
                sql += " AND benefit_category LIKE %s"
                benefit_term = f"%{benefit_param}%"
                query_args.append(benefit_term)
                
            results = db.fetch_all(sql, tuple(query_args))
            db.close()
            
            return jsonify({
                "status": "success",
                "count": len(results),
                "data": results
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
            return redirect(url_for("auth.shop")) # Matches your blueprint routing namespace perfectly
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