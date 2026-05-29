from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
            
        if session.get("role") != "admin":
            flash("Unauthorized access. Admin privileges required.", "danger")
            return redirect(url_for("auth.home")) 
            
        return f(*args, **kwargs)
    return decorated

def merchant_required(f):
    """Protects seller-specific routes like the Merchant Dashboard and Inventory"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("auth.login"))
            
        # Allowing both merchants AND admins to view merchant pages
        if session.get("role") not in ["merchant", "admin"]:
            flash("Unauthorized. A merchant account is required to sell herbs.", "danger")
            return redirect(url_for("auth.home"))
            
        return f(*args, **kwargs)
    return decorated