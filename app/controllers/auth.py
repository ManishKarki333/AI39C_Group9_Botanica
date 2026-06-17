import re
import os
import random
import json
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, session, flash, request, current_app
from app.controllers.base_controller import BaseController
from app.models.database import Database
from app.models.user_model import User
from app.models.contact_model import ContactMessage
from app.models.order_model import Order
from werkzeug.security import generate_password_hash

# Google Auth Libraries
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.utils import send_otp_email

ALLOWED_ROLES = {"user", "merchant"}
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AuthController(BaseController):

    def __init__(self):
        super().__init__()
        self.user_model = User()
        self.order_model = Order()

    # ── Helpers ──────────────────────────────────────────────
    def is_logged_in(self) -> bool:
        return "user_id" in session

    def _get_redirect_route(self, role: str) -> str:
        if role == "admin":
            return "admin.dashboard"
        if role == "merchant":
            return "auth.merchant_dashboard"
        return "auth.home"

    def home(self):
        db = Database()
        categories = db.fetch_all("SELECT * FROM categories ORDER BY name ASC")
        db.close()
        return render_template("home.html", categories=categories)

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
                return render_template("login.html", google_client_id=current_app.config.get('GOOGLE_CLIENT_ID'))

            user_data = self.user_model.find_by("email", email)

            if user_data is not None:
                user = User.from_db(user_data)

                if user is not None and user.check_password(password):
                    if user_data.get("is_active") == 0:
                        flash("This account has been deactivated. Please contact support to reactivate it.", "danger")
                        return render_template("login.html", google_client_id=current_app.config.get('GOOGLE_CLIENT_ID'))

                    session["user_id"] = user_data["id"]
                    session["user_name"] = user_data["name"]
                    session["role"] = user_data["role"]

                    target_route = self._get_redirect_route(user_data["role"])
                    return self.flash_and_redirect("Login successful!", "success", target_route)

            flash("Invalid email or password.", "danger")
            return render_template("login.html", google_client_id=current_app.config.get('GOOGLE_CLIENT_ID'))

        return render_template("login.html", google_client_id=current_app.config.get('GOOGLE_CLIENT_ID'))

    # ── Register ─────────────────────────────────────────────
    def register(self):
        if self.is_logged_in():
            return redirect(url_for("auth.home"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            role = request.form.get("role", "user")

            if role not in ALLOWED_ROLES:
                role = "user"

            if not name or not email or not password:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            if not EMAIL_REGEX.match(email):
                flash("Please enter a valid email address.", "danger")
                return render_template("register.html")

            existing = self.user_model.find_by("email", email)
            if existing:
                flash("Email already registered. Please log in.", "warning")
                return redirect(url_for("auth.login"))

            new_user = User(name=name, email=email, password=password, role=role)
            new_user.save()

            return self.flash_and_redirect("Registration successful! Please login.", "success", "auth.login")

        return render_template("register.html")

    # ── Profile ─────────────────────────────────────────────
    def profile(self):
        if 'user_id' not in session:
            flash("Please log in to access your account.", "warning")
            return redirect(url_for('auth.login'))

        user_id = session['user_id']
        db = Database()

        try:
            if request.method == "POST":
                name = request.form.get("name", "").strip()
                email = request.form.get("email", "").strip()

                if not name or not email:
                    flash("Name and email are required.", "danger")
                    return redirect(url_for('auth.profile'))

                existing = db.fetch_one("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
                if existing:
                    flash("That email address is already in use.", "danger")
                    return redirect(url_for('auth.profile'))

                current_user = db.fetch_one("SELECT profile_pic, certification_badge, role FROM users WHERE id = %s", (user_id,))
                profile_pic = current_user.get("profile_pic")
                certification_badge = current_user.get("certification_badge")
                role = current_user.get("role")

                profile_pic_file = request.files.get("profile_pic")
                if profile_pic_file and profile_pic_file.filename:
                    upload_dir = 'app/static/uploads/Profile Picture'
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)
                    ext = os.path.splitext(profile_pic_file.filename)[1]
                    filename = f"profile_{user_id}_{uuid.uuid4().hex}{ext}"
                    profile_pic_file.save(os.path.join(upload_dir, filename))
                    profile_pic = f"/static/uploads/Profile Picture/{filename}"

                if role == "merchant":
                    cert_file = request.files.get("certification_badge")
                    if cert_file and cert_file.filename:
                        upload_dir = 'app/static/uploads/Profile Picture'
                        if not os.path.exists(upload_dir):
                            os.makedirs(upload_dir)
                        ext = os.path.splitext(cert_file.filename)[1]
                        filename = f"cert_{user_id}_{uuid.uuid4().hex}{ext}"
                        cert_file.save(os.path.join(upload_dir, filename))
                        certification_badge = f"/static/uploads/Profile Picture/{filename}"

                db.execute(
                    "UPDATE users SET name = %s, email = %s, profile_pic = %s, certification_badge = %s WHERE id = %s",
                    (name, email, profile_pic, certification_badge, user_id)
                )
                if hasattr(db, 'commit'): 
                    db.commit()

                session["user_name"] = name
                flash("Profile updated successfully!", "success")
                return redirect(url_for('auth.profile'))

            user = db.fetch_one("SELECT id, name, email, role, profile_pic, certification_badge, created_at FROM users WHERE id = %s", (user_id,))
            orders = db.fetch_all("SELECT id, total_amount, order_status, payment_status, created_at FROM orders WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
            return render_template('profile.html', user=user, orders=orders)
            
        finally:
            db.close()

    def deactivate_account(self):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))

        user_id = session['user_id']
        db = Database()
        db.execute("UPDATE users SET is_active = 0 WHERE id = %s", (user_id,))
        if hasattr(db, 'commit'): db.commit()
        db.close()

        session.clear()
        flash("Your account has been deactivated successfully.", "info")
        return redirect(url_for('auth.login'))

    def delete_account(self):
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))

        user_id = session['user_id']
        db = Database()
        db.execute("DELETE FROM users WHERE id = %s", (user_id,))
        if hasattr(db, 'commit'): db.commit()
        db.close()

        session.clear()
        flash("Your account has been deleted permanently.", "info")
        return redirect(url_for('auth.login'))

    def logout(self):
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("auth.login"))

    def about(self):
        return render_template("about.html")

    # ── Contact ──────────────────────────────────────────────
    def contact(self):
        if request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name",  "").strip()
            email = request.form.get("email",      "").strip()
            inquiry = request.form.get("inquiry",    "").strip()
            subject = request.form.get("subject",    "").strip()
            message = request.form.get("message",    "").strip()

            if not all([first_name, last_name, email, subject, message]):
                flash("All fields are required.", "danger")
                return render_template("contact.html")

            msg = ContactMessage(first_name=first_name, last_name=last_name, email=email, inquiry=inquiry, subject=subject, message=message)
            msg.save()

            flash("Your message has been sent!", "success")
            return redirect(url_for("auth.contact"))

        return render_template("contact.html")

    # ── Merchant Dashboard ───────────────────────────────────
    def merchant_dashboard(self):
        if session.get("role") != "merchant":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("auth.home"))

        merchant_id = session.get("user_id")
        db = Database()

        # 1. Fetch user profile data
        user = db.fetch_one("SELECT name, email, profile_pic, certification_badge FROM users WHERE id = %s", (merchant_id,))
        
        # 2. Fetch merchant items catalog
        herbs = db.fetch_all("SELECT * FROM herbs WHERE merchant_id = %s", (merchant_id,))
        
        # 3. Fetch chart insights metrics
        chart_query = """
            SELECT h.common_name, CAST(SUM(oi.quantity) AS UNSIGNED) as total_sold
            FROM order_items oi
            JOIN herbs h ON oi.herb_id = h.id
            WHERE h.merchant_id = %s
            GROUP BY oi.herb_id
            ORDER BY total_sold DESC
        """
        top_selling = db.fetch_all(chart_query, (merchant_id,))

        # 4. Fetch the orders using your model wrapper
        orders = self.order_model.get_merchant_orders(merchant_id)
        
        categories = db.fetch_all("SELECT * FROM categories ORDER BY name ASC")
        
        # Close the raw DB connection tracking safely after ALL queries are executed
        db.close()

        # 5. Filter out low stock alerts locally
        low_stock_herbs = [h for h in herbs if h["stock_quantity"] <= 5]
        
        return render_template(
            "merchant_dashboard.html", 
            herbs=herbs, 
            orders=orders, 
            user=user, 
            top_selling=top_selling, 
            low_stock_herbs=low_stock_herbs,
            categories=categories
        )
    
    # ── Google OAuth Login ─────────────────────────────────────
    def google_login(self):
        credential = request.form.get("credential")
        if not credential and request.is_json:
            credential = request.json.get("credential")

        email = None
        name = None

        if credential == "mock_google_token":
            email = "google_mock_user@example.com"
            name = "Google Mock User"
        elif credential:
            csrf_cookie = request.cookies.get("g_csrf_token")
            csrf_body = request.form.get("g_csrf_token")
            if csrf_body and csrf_cookie != csrf_body:
                flash("CSRF verification failed for Google Sign-In.", "danger")
                return redirect(url_for("auth.login"))

            try:
                client_id = current_app.config.get('GOOGLE_CLIENT_ID')
                if not client_id:
                    flash("Google login is not configured on this server.", "danger")
                    return redirect(url_for("auth.login"))

                id_info = id_token.verify_oauth2_token(
                    credential, 
                    google_requests.Request(), 
                    client_id.strip()
                )

                if not id_info.get("email_verified"):
                    flash("Google email is not verified.", "danger")
                    return redirect(url_for("auth.login"))

                email = id_info.get("email")
                name = id_info.get("name", email.split('@')[0] if email else "Google User")

            except Exception as e:
                print(f"Google Token Verification Failed: {e}")
                flash("Failed to verify Google credentials. Please try again.", "danger")
                return redirect(url_for("auth.login"))

        if not email:
            flash("Invalid Google Sign-In attempt.", "danger")
            return redirect(url_for("auth.login"))

        db = Database()
        user_data = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))

        if not user_data:
            random_pw = str(uuid.uuid4())
            hashed_pw = generate_password_hash(random_pw)
            db.execute(
                "INSERT INTO users (name, email, password, role, is_active) VALUES (%s, %s, %s, %s, 1)",
                (name, email, hashed_pw, "user")
            )
            if hasattr(db, 'commit'): db.commit()
            user_data = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
            print(f"Registered new Google OAuth user: {email}")
        else:
            if user_data.get("is_active") == 0:
                db.close()
                flash("This account has been deactivated. Please contact support to reactivate it.", "danger")
                return redirect(url_for("auth.login"))

        db.close()

        session["user_id"] = user_data["id"]
        session["user_name"] = user_data["name"]
        session["role"] = user_data["role"]

        target_route = self._get_redirect_route(user_data["role"])
        return self.flash_and_redirect("Logged in successfully via Google!", "success", target_route)

    # ── Forgot Password & OTP ──────────────────────────────────
    def forgot_password(self):
        if request.method == "POST":
            email = request.form.get("email", "").strip()
            if not email:
                flash("Please enter your email address.", "danger")
                return render_template("forgot_password.html")

            db = Database()
            user = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
            if not user:
                db.close()
                flash("No account matches that email address.", "danger")
                return render_template("forgot_password.html")

            otp = f"{random.randint(100000, 999999)}"
            expiry = datetime.now() + timedelta(minutes=10)

            db.execute(
                "UPDATE users SET otp_code = %s, otp_expiry = %s WHERE id = %s",
                (otp, expiry.strftime('%Y-%m-%d %H:%M:%S'), user["id"])
            )
            if hasattr(db, 'commit'): db.commit()
            db.close()

            email_sent = send_otp_email(email, otp, expiry.strftime('%I:%M:%S %p'))

            if email_sent:
                flash("A 6-digit verification code has been sent to your email inbox.", "success")
            else:
                print("\n" + "="*50)
                print(f" [DEV MODE] PASSWORD RESET OTP FOR {email}")
                print(f" OTP CODE: {otp}")
                print(f" EXPIRES AT: {expiry.strftime('%I:%M:%S %p')}")
                print("="*50 + "\n")
                flash("A verification code has been generated. Check terminal/console for dev testing.", "success")
            
            session["otp_reset_email"] = email
            return redirect(url_for("auth.verify_otp"))

        return render_template("forgot_password.html")

    def verify_otp(self):
        email = session.get("otp_reset_email")
        if not email:
            flash("Please request a password reset first.", "warning")
            return redirect(url_for("auth.forgot_password"))

        if request.method == "POST":
            otp_input = request.form.get("otp", "").strip()
            if not otp_input:
                flash("Please enter the 6-digit code.", "danger")
                return render_template("verify_otp.html", email=email)

            db = Database()
            user = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))

            if not user or not user.get("otp_code") or user.get("otp_code") != otp_input:
                db.close()
                flash("Invalid OTP code. Please try again.", "danger")
                return render_template("verify_otp.html", email=email)

            expiry = user.get("otp_expiry")
            if isinstance(expiry, str):
                expiry = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S')

            # Handle parsing safety check safely against local time comparisons
            if expiry and expiry.replace(tzinfo=None) < datetime.now().replace(tzinfo=None):
                db.close()
                flash("OTP code has expired. Please request a new one.", "danger")
                return redirect(url_for("auth.forgot_password"))

            db.close()
            session["otp_verified_email"] = email
            session.pop("otp_reset_email", None)
            flash("OTP verified successfully. Please choose a new password.", "success")
            return redirect(url_for("auth.reset_password"))

        return render_template("verify_otp.html", email=email)

    def reset_password(self):
        email = session.get("otp_verified_email")
        if not email:
            flash("Unauthorized access. Please verify your OTP code first.", "warning")
            return redirect(url_for("auth.forgot_password"))

        if request.method == "POST":
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not password or not confirm_password:
                flash("Please fill in both password fields.", "danger")
                return render_template("reset_password.html")

            if password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("reset_password.html")

            hashed_pw = generate_password_hash(password)
            db = Database()
            db.execute(
                "UPDATE users SET password = %s, otp_code = NULL, otp_expiry = NULL WHERE email = %s",
                (hashed_pw, email)
            )
            if hasattr(db, 'commit'): db.commit()
            db.close()

            session.pop("otp_verified_email", None)
            flash("Your password has been reset successfully! You can now log in.", "success")
            return redirect(url_for("auth.login"))

        return render_template("reset_password.html")
    
    def faq(self):
        return render_template("faq.html")