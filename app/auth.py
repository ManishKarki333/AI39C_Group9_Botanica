from flask import session, redirect, url_for, flash
from werkzeug.wrappers import Response  # ✅ import from werkzeug directly
from functools import wraps
from typing import Callable


def login_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated(*args, **kwargs) -> Response:  # ✅ now matches what redirect() returns
        if "user_id" not in session:
            flash("Please log in first to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated(*args, **kwargs) -> Response:
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") != "admin":
            flash("Unauthorized access. Admin privileges required.", "danger")
            return redirect(url_for("auth.home"))
        return f(*args, **kwargs)
    return decorated


def merchant_required(f: Callable) -> Callable:
    @wraps(f)
    def decorated(*args, **kwargs) -> Response:
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        if session.get("role") not in ["merchant", "admin"]:
            flash("Unauthorized. A merchant account is required to sell herbs.", "danger")
            return redirect(url_for("auth.home"))
        return f(*args, **kwargs)
    return decorated
