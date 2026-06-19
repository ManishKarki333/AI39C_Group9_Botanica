from app import create_app
from app.models.database import Database
from config import SECRET_KEY

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