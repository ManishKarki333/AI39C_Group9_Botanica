import os
from flask import render_template, request, redirect, url_for, flash, session
from app.controllers.base_controller import BaseController
from app.models.database import Database


class AdminController(BaseController):
    def __init__(self):
        super().__init__()

    def dashboard(self):
        db = Database()
        try:
            # 1. Fetch Stats Metrics
            total_users = db.fetch_one("SELECT COUNT(*) as count FROM users WHERE role = 'user'")["count"]
            total_merchants = db.fetch_one("SELECT COUNT(*) as count FROM users WHERE role = 'merchant'")["count"]
            total_products = db.fetch_one("SELECT COUNT(*) as count FROM herbs")["count"]
            active_accounts = db.fetch_one("SELECT COUNT(*) as count FROM users WHERE is_active = 1")["count"]
            inactive_accounts = db.fetch_one("SELECT COUNT(*) as count FROM users WHERE is_active = 0")["count"]
            total_reports = db.fetch_one("SELECT COUNT(*) as count FROM reports WHERE status = 'pending'")["count"]
            
            # Additional platform activity statistics
            total_orders = db.fetch_one("SELECT COUNT(*) as count FROM orders")["count"]
            revenue_data = db.fetch_one("SELECT SUM(total_amount) as total FROM orders WHERE payment_status = 'Paid'")
            total_revenue = float(revenue_data["total"]) if revenue_data and revenue_data["total"] else 0.0

            # 2. Fetch Users & Merchants list
            users = db.fetch_all("SELECT * FROM users WHERE role != 'admin' ORDER BY created_at DESC")

            # 3. Fetch Products with Merchant info
            products = db.fetch_all("""
                SELECT h.*, u.name as merchant_name 
                FROM herbs h 
                LEFT JOIN users u ON h.merchant_id = u.id 
                ORDER BY h.created_at DESC
            """)

            # 4. Fetch Categories
            categories = db.fetch_all("SELECT * FROM categories ORDER BY name ASC")

            # 5. Fetch Reports (flagged reviews/products/merchants)
            reports = db.fetch_all("""
                SELECT r.*, u.name as reporter_name, h.common_name as product_name, h.image_url as product_image, m.name as merchant_name 
                FROM reports r 
                JOIN users u ON r.user_id = u.id 
                LEFT JOIN herbs h ON r.target_type = 'product' AND r.target_id = h.id 
                LEFT JOIN users m ON (r.target_type = 'merchant' AND r.target_id = m.id) 
                                  OR (r.target_type = 'product' AND h.merchant_id = m.id)
                ORDER BY r.created_at DESC
            """)

            # 6. Fetch Recent Platform Activities
            recent_orders = db.fetch_all("""
                SELECT o.*, u.name as customer_name 
                FROM orders o 
                JOIN users u ON o.user_id = u.id 
                ORDER BY o.created_at DESC LIMIT 5
            """)

        finally:
            db.close()

        return render_template(
            "admin_dashboard.html",
            total_users=total_users,
            total_merchants=total_merchants,
            total_products=total_products,
            active_accounts=active_accounts,
            inactive_accounts=inactive_accounts,
            total_reports=total_reports,
            total_orders=total_orders,
            total_revenue=total_revenue,
            users=users,
            products=products,
            categories=categories,
            reports=reports,
            recent_orders=recent_orders
        )

    def users_list(self):
        return redirect(url_for("admin.dashboard") + "#users")

    def toggle_user_status(self, user_id):
        db = Database()
        try:
            user = db.fetch_one("SELECT is_active, name FROM users WHERE id = %s", (user_id,))
            if user:
                new_status = 0 if user["is_active"] == 1 else 1
                db.execute("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id))
                action_word = "suspended" if new_status == 0 else "reactivated"
                flash(f"Account for user '{user['name']}' has been {action_word}.", "success")
        except Exception as e:
            print("Toggle User Status Error:", e)
            flash("Failed to update user account status.", "danger")
        finally:
            db.close()
        return redirect(url_for("admin.dashboard") + "#users")

    def delete_user_account(self, user_id):
        db = Database()
        try:
            user = db.fetch_one("SELECT name FROM users WHERE id = %s", (user_id,))
            if user:
                # Retrieve merchant's products to delete images first
                products = db.fetch_all("SELECT image_url FROM herbs WHERE merchant_id = %s", (user_id,))
                for p in products:
                    if p.get("image_url") and 'default_herb.png' not in p["image_url"]:
                        try:
                            path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), p["image_url"].lstrip('/'))
                            if os.path.exists(path):
                                os.remove(path)
                        except Exception:
                            pass
                db.execute("DELETE FROM users WHERE id = %s", (user_id,))
                flash(f"Account '{user['name']}' and all associated listings deleted permanently.", "success")
        except Exception as e:
            print("Delete User Error:", e)
            flash("Failed to delete user account.", "danger")
        finally:
            db.close()
        return redirect(url_for("admin.dashboard") + "#users")

    def merchant_detail(self, merchant_id):
        # Allow viewing specific merchant's products by redirecting and filtering product list
        return redirect(url_for("admin.dashboard", filter_merchant=merchant_id) + "#products")

    def products_list(self):
        return redirect(url_for("admin.dashboard") + "#products")

    def delete_product(self, product_id):
        db = Database()
        try:
            herb = db.fetch_one("SELECT image_url, common_name FROM herbs WHERE id = %s", (product_id,))
            if herb:
                if herb.get("image_url") and 'default_herb.png' not in herb["image_url"]:
                    try:
                        path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), herb["image_url"].lstrip('/'))
                        if os.path.exists(path):
                            os.remove(path)
                    except Exception as img_err:
                        print("Error removing product image file:", img_err)
                db.execute("DELETE FROM herbs WHERE id = %s", (product_id,))
                flash(f"Product '{herb['common_name']}' deleted successfully.", "success")
        except Exception as e:
            print("Delete Product Error:", e)
            flash("Failed to delete product.", "danger")
        finally:
            db.close()
        return redirect(url_for("admin.dashboard") + "#products")

    def categories_list(self):
        return redirect(url_for("admin.dashboard") + "#categories")

    def add_category(self):
        name = request.form.get("name", "").strip()
        if not name:
            flash("Category name cannot be empty.", "danger")
            return redirect(url_for("admin.dashboard") + "#categories")

        db = Database()
        try:
            db.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
            flash(f"Category '{name}' created successfully.", "success")
        except Exception:
            flash("Category name already exists.", "danger")
        finally:
            db.close()
        return redirect(url_for("admin.dashboard") + "#categories")

    def edit_category(self, cat_id):
        name = request.form.get("name", "").strip()
        if not name:
            flash("Category name cannot be empty.", "danger")
            return redirect(url_for("admin.dashboard") + "#categories")

        db = Database()
        try:
            old_cat = db.fetch_one("SELECT name FROM categories WHERE id = %s", (cat_id,))
            if old_cat:
                db.execute("UPDATE categories SET name = %s WHERE id = %s", (name, cat_id))
                db.execute("UPDATE herbs SET benefit_category = %s WHERE benefit_category = %s", (name, old_cat["name"]))
                flash("Category updated successfully.", "success")
        except Exception as e:
            print("Edit Category Error:", e)
            flash("Failed to update category name.", "danger")
        finally:
            db.close()
        return redirect(url_for("admin.dashboard") + "#categories")

    def delete_category(self, cat_id):
        db = Database()
        try:
            cat = db.fetch_one("SELECT name FROM categories WHERE id = %s", (cat_id,))
            if cat:
                # Check for products associated with this category
                herbs_count = db.fetch_one("SELECT COUNT(*) as count FROM herbs WHERE benefit_category = %s", (cat["name"],))["count"]
                if herbs_count > 0:
                    flash(f"Cannot delete category '{cat['name']}'. There are {herbs_count} product(s) associated with it.", "danger")
                else:
                    db.execute("DELETE FROM categories WHERE id = %s", (cat_id,))
                    flash("Category removed successfully.", "success")
        except Exception as e:
            print("Delete Category Error:", e)
            flash("Failed to delete category.", "danger")
        finally:
            db.close()
        return redirect(url_for("admin.dashboard") + "#categories")

    def reports_list(self):
        return redirect(url_for("admin.dashboard") + "#reports")

    def resolve_report(self, report_id):
        db = Database()
        try:
            db.execute("UPDATE reports SET status = 'resolved' WHERE id = %s", (report_id,))
            flash("Report marked as resolved.", "success")
        except Exception as e:
            print("Resolve Report Error:", e)
            flash("Failed to resolve report.", "danger")
        finally:
            db.close()
        return redirect(url_for("admin.dashboard") + "#reports")
