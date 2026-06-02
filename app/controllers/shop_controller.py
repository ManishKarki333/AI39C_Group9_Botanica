import uuid
import os
from flask import render_template, request, session, redirect, url_for, flash
from app.controllers.base_controller import BaseController
from app.models.database import Database

class ShopController(BaseController):
    
    def shop(self):
        """Handle the main marketplace grid."""
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

    def herb_library(self):
        """Fetch all herbs for the reference library."""
        db = Database()
        herbs = db.fetch_all("SELECT * FROM herbs")
        db.close()
        return render_template("herb_library.html", herbs=herbs)

    def herb_details(self, id):
        """Fetch details for a specific herb."""
        db = Database()
        herb = db.fetch_one("SELECT * FROM herbs WHERE id = %s", (id,))
        db.close()
        if not herb:
            flash("Herb not found.", "danger")
            return redirect(url_for("auth.shop"))
        return render_template("herb_details.html", herb=herb)

    def add_product(self):
        if session.get("role") != "merchant":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("auth.login"))

        if request.method == "POST":
            # 1. Gather data
            common_name = request.form.get("common_name", "").strip()
            scientific_name = request.form.get("scientific_name", "").strip()
            description = request.form.get("description", "").strip()
            price = request.form.get("price", 0)
            benefit_category = request.form.get("benefit_category", "")
            stock_quantity = request.form.get("stock_quantity", 0)
            
            # 2. Handle File Upload
            product_image = request.files.get('product_image')
            image_url = '/static/uploads/default_herb.png' 
            
            if product_image and product_image.filename:
                # Ensure uploads directory exists
                upload_dir = 'app/static/uploads'
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                    
                ext = os.path.splitext(product_image.filename)[1]
                unique_filename = f"{uuid.uuid4().hex}{ext}"
                save_path = os.path.join(upload_dir, unique_filename)
                product_image.save(save_path)
                image_url = f'/static/uploads/{unique_filename}'

            # 3. Database operation
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