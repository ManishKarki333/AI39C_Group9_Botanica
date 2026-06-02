# ============================================================
#  AuthController — Handles all authentication & page routes
# ============================================================
from flask import render_template, redirect, url_for, session, flash, request
from app.controllers.base_controller import BaseController
from app.models.database import Database
from app.models.user_model import User
from app.models.contact_model import ContactMessage


class AuthController(BaseController):
    def __init__(self):
        self.user_model = User()

    # ── Home ────────────────────────────────────────────────
    def home(self):
        return render_template("home.html")

    # ── Role-based redirect helper ───────────────────────────
    def _get_redirect_route(self, role):
        """Determine landing route based on user role."""
        if role == "admin":
            return "auth.dashboard"
        elif role == "merchant":
            return "auth.merchant_dashboard"
        else:
            # customer / user default landing page
            return "auth.home"

    # ── Login ────────────────────────────────────────────────
    def login(self):
        if self.is_logged_in():
            current_role = session.get("role", "user")
            return redirect(url_for(self._get_redirect_route(current_role)))

        if request.method == "POST":
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Email and password are required.", "danger")
                return render_template("login.html")

            user_data = self.user_model.find_by("email", email)

            if user_data:
                user = User.from_db(user_data)

                if user.check_password(password):
                    session["user_id"] = user_data["id"]
                    session["user_name"] = user_data["name"]
                    session["role"] = user_data["role"]

                    target_route = self._get_redirect_route(user_data["role"])
                    return self.flash_and_redirect(
                        "Login successful!", "success", target_route
                    )

            flash("Invalid email or password.", "danger")
        return render_template("login.html")

    # ── Merchant Dashboard ───────────────────────────────────
    def merchant_dashboard(self):
        if not self.is_logged_in() or session.get("role") != "merchant":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("auth.login"))

        db = Database()
        merchant_id = session.get("user_id")
        merchant_herbs = db.fetch_all(
            "SELECT * FROM herbs WHERE merchant_id = %s",
            (merchant_id,)
        )
        db.close()

        return render_template("merchant_dashboard.html", herbs=merchant_herbs)

    # ── Register ─────────────────────────────────────────────
    def register(self):
        if self.is_logged_in():
            current_role = session.get("role", "user")
            return redirect(url_for(self._get_redirect_route(current_role)))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            role = request.form.get("role", "user").strip().lower()

            # Keep role naming consistent with database/app logic
            if role == "customer":
                role = "user"

            if role not in ["user", "merchant"]:
                role = "user"

            if not name or not email or not password:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            if len(name) > 100:
                flash("Name must be under 100 characters.", "danger")
                return render_template("register.html")

            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("register.html")

            new_user = User(name=name, email=email, password=password, role=role)

            if new_user.email_exists():
                flash("Email already exists.", "danger")
                return redirect(url_for("auth.register"))

            new_user.save()
            return self.flash_and_redirect(
                "Registration successful! Please login.",
                "success",
                "auth.login"
            )

        return render_template("register.html")

    # ── Logout ───────────────────────────────────────────────
    def logout(self):
        session.clear()
        return self.flash_and_redirect(
            "You have been logged out.", "success", "auth.login"
        )

    # ── About ────────────────────────────────────────────────
    def about(self):
        return render_template("about.html")

    # ── Contact ──────────────────────────────────────────────
    def contact(self):
        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            email = request.form.get("email", "").strip()
            inquiry = request.form.get("inquiry", "").strip()
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()

            if not first_name or not last_name or not email or not subject or not message:
                flash("Please fill in all required fields.", "danger")
                return render_template("contact.html")

            if "@" not in email or "." not in email:
                flash("Please enter a valid email address.", "danger")
                return render_template("contact.html")

            contact_msg = ContactMessage(
                first_name=first_name,
                last_name=last_name,
                email=email,
                inquiry=inquiry,
                subject=subject,
                message=message,
            )
            contact_msg.save()

            flash(
                f"Thank you {first_name}! Your message has been sent. We'll reply within 24 hours.",
                "success",
            )
            return redirect(url_for("auth.contact"))

        return render_template("contact.html")
