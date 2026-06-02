import re
from flask import (
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request,
)
from app.models.user_model import User
from app.models.contact_model import ContactMessage

# ✅ Security: whitelist of self-registerable roles
ALLOWED_ROLES  = {"user", "merchant"}
# ✅ Basic email format validator
EMAIL_REGEX    = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthController:

    def __init__(self):
        self.user_model = User()

    # ── Helpers ──────────────────────────────────────────────
    def is_logged_in(self) -> bool:
        return "user_id" in session

    def _get_redirect_route(self, role: str) -> str:
        if role == "admin":
            return "admin.dashboard"
        if role == "merchant":
            return "auth.merchant_dashboard"
        return "auth.home"

    # ── Home ─────────────────────────────────────────────────
    def home(self):
        return render_template("home.html")

    # ── Login ────────────────────────────────────────────────
    def login(self):
        if self.is_logged_in():
            current_role = session.get("role", "user")
            return redirect(url_for(self._get_redirect_route(current_role)))

        if request.method == "POST":
            email    = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Email and password are required.", "danger")
                return render_template("login.html")

            user_data = self.user_model.find_by("email", email)

            if user_data is not None:
                user = User.from_db(user_data)

                if user is not None and user.check_password(password):
                    session["user_id"]   = user_data["id"]
                    session["user_name"] = user_data["name"]
                    session["role"]      = user_data["role"]

                    flash("Login successful!", "success")
                    return redirect(url_for(self._get_redirect_route(user_data["role"])))

            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        return render_template("login.html")

    # ── Register ─────────────────────────────────────────────
    def register(self):
        if self.is_logged_in():
            return redirect(url_for("auth.home"))

        if request.method == "POST":
            name     = request.form.get("name", "").strip()
            email    = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            role     = request.form.get("role", "user")

            # ✅ Sanitize role — never trust user input
            if role not in ALLOWED_ROLES:
                role = "user"

            if not name or not email or not password:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            # ✅ Validate email format
            if not EMAIL_REGEX.match(email):
                flash("Please enter a valid email address.", "danger")
                return render_template("register.html")

            existing = self.user_model.find_by("email", email)
            if existing:
                flash("Email already registered. Please log in.", "warning")
                return redirect(url_for("auth.login"))

            new_user = User(name=name, email=email, password=password, role=role)
            new_user.save()

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))

        return render_template("register.html")

    # ── Logout ───────────────────────────────────────────────
    def logout(self):
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("auth.login"))

    # ── About ────────────────────────────────────────────────
    def about(self):
        return render_template("about.html")

    # ── Contact ──────────────────────────────────────────────
    def contact(self):
        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name  = request.form.get("last_name",  "").strip()
            email      = request.form.get("email",      "").strip()
            inquiry    = request.form.get("inquiry",    "").strip()
            subject    = request.form.get("subject",    "").strip()
            message    = request.form.get("message",    "").strip()

            if not all([first_name, last_name, email, subject, message]):
                flash("All fields are required.", "danger")
                return render_template("contact.html")

            msg = ContactMessage(
                first_name=first_name,
                last_name=last_name,
                email=email,
                inquiry=inquiry,
                subject=subject,
                message=message,
            )
            msg.save()

            flash("Your message has been sent!", "success")
            return redirect(url_for("auth.contact"))

        return render_template("contact.html")

    # ── Merchant Dashboard ───────────────────────────────────
    def merchant_dashboard(self):
        return render_template("merchant_dashboard.html")
