import re
import os
import random
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, session, flash, request
from app.controllers.base_controller import BaseController
from app.models.database import Database
from app.models.user_model import User
from app.models.contact_model import ContactMessage
from app.models.order_model import Order
from werkzeug.security import generate_password_hash
import config


def send_otp_email(recipient_email, otp_code, expiry_time):
    """Send OTP code via Gmail SMTP. Returns True on success, False on failure."""
    sender_email = config.SMTP_EMAIL
    sender_password = config.SMTP_PASSWORD
    smtp_server = config.SMTP_SERVER
    smtp_port = config.SMTP_PORT

    if not sender_email or not sender_password:
        return False  # SMTP not configured, caller should fallback

    subject = "Botanica - Your Password Reset Code"

    html_body = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #2f855a, #1a3a2a); padding: 30px 24px; text-align: center;">
            <h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 700;">Botanica</h1>
            <p style="color: #c6f6d5; margin: 6px 0 0; font-size: 14px;">Herbal Marketplace</p>
        </div>
        <div style="padding: 32px 24px;">
            <h2 style="color: #1a202c; margin: 0 0 12px; font-size: 20px;">Password Reset Request</h2>
            <p style="color: #4a5568; font-size: 14px; line-height: 1.6; margin: 0 0 24px;">
                We received a request to reset your password. Use the verification code below to proceed:
            </p>
            <div style="background: #f0fff4; border: 2px dashed #2f855a; border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 24px;">
                <span style="font-size: 36px; font-weight: 700; letter-spacing: 8px; color: #2f855a;">{otp_code}</span>
            </div>
            <p style="color: #718096; font-size: 13px; margin: 0 0 8px;">
                This code expires at <strong>{expiry_time}</strong> (10 minutes from now).
            </p>
            <p style="color: #a0aec0; font-size: 12px; margin: 24px 0 0; border-top: 1px solid #e2e8f0; padding-top: 16px;">
                If you did not request this, please ignore this email. Your password will remain unchanged.
            </p>
        </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Botanica <{sender_email}>"
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"[EMAIL] OTP sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send OTP email: {e}")
        return False

# Security: whitelist of self-registerable roles
ALLOWED_ROLES = {"user", "merchant"}
# Basic email format validator
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
                return render_template("login.html", google_client_id=config.GOOGLE_CLIENT_ID)

            user_data = self.user_model.find_by("email", email)

            if user_data is not None:
                user = User.from_db(user_data)

                if user is not None and user.check_password(password):
                    if user.is_active == 0:
                        flash("This account has been deactivated. Please contact support to reactivate it.", "danger")
                        return render_template("login.html", google_client_id=config.GOOGLE_CLIENT_ID)

                    session["user_id"]   = user_data["id"]
                    session["user_name"] = user_data["name"]
                    session["role"]      = user_data["role"]
                    
                    # Dynamic backend routing based on database role matrix
                    target_route = self._get_redirect_route(user_data["role"])
                    return self.flash_and_redirect(
                        "Login successful!", "success", target_route
                    )

            flash("Invalid email or password.", "danger")
            return render_template("login.html", google_client_id=config.GOOGLE_CLIENT_ID)

        return render_template("login.html", google_client_id=config.GOOGLE_CLIENT_ID)

    # ── Register ─────────────────────────────────────────────
    def register(self):
        if self.is_logged_in():
            return redirect(url_for("auth.home"))

        if request.method == "POST":
            name     = request.form.get("name", "").strip()
            email    = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            role     = request.form.get("role", "user")

            # Sanitize role — never trust user input
            if role not in ALLOWED_ROLES:
                role = "user"

            if not name or not email or not password:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            # Validate email format
            if not EMAIL_REGEX.match(email):
                flash("Please enter a valid email address.", "danger")
                return render_template("register.html")

            existing = self.user_model.find_by("email", email)
            if existing:
                flash("Email already registered. Please log in.", "warning")
                return redirect(url_for("auth.login"))

            new_user = User(name=name, email=email, password=password, role=role)
            new_user.save()
            
            return self.flash_and_redirect(
                "Registration successful! Please login.", "success", "auth.login"
            )

        return render_template("register.html")
    
    # ── Profile ─────────────────────────────────────────────
    def profile(self):
        """Render and handle user account profile settings and order history."""
        if 'user_id' not in session:
            flash("Please log in to access your account.", "warning")
            return redirect(url_for('auth.login'))
            
        user_id = session['user_id']
        db = Database()
        
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            
            if not name or not email:
                flash("Name and email are required.", "danger")
                db.close()
                return redirect(url_for('auth.profile'))
                
            # Check if email is already in use by another user
            existing = db.fetch_one("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
            if existing:
                flash("That email address is already in use.", "danger")
                db.close()
                return redirect(url_for('auth.profile'))
                
            # Fetch current user details to keep files if not updated
            current_user = db.fetch_one("SELECT profile_pic, certification_badge, role FROM users WHERE id = %s", (user_id,))
            profile_pic = current_user.get("profile_pic")
            certification_badge = current_user.get("certification_badge")
            role = current_user.get("role")
            
            # Handle profile pic upload
            profile_pic_file = request.files.get("profile_pic")
            if profile_pic_file and profile_pic_file.filename:
                upload_dir = 'app/static/uploads'
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                ext = os.path.splitext(profile_pic_file.filename)[1]
                filename = f"profile_{user_id}_{uuid.uuid4().hex}{ext}"
                profile_pic_file.save(os.path.join(upload_dir, filename))
                profile_pic = f"/static/uploads/{filename}"
                
            # Handle certificate badge upload
            if role == "merchant":
                cert_file = request.files.get("certification_badge")
                if cert_file and cert_file.filename:
                    upload_dir = 'app/static/uploads'
                    if not os.path.exists(upload_dir):
                        os.makedirs(upload_dir)
                    ext = os.path.splitext(cert_file.filename)[1]
                    filename = f"cert_{user_id}_{uuid.uuid4().hex}{ext}"
                    cert_file.save(os.path.join(upload_dir, filename))
                    certification_badge = f"/static/uploads/{filename}"
            
            # Update user info in db
            db.execute(
                "UPDATE users SET name = %s, email = %s, profile_pic = %s, certification_badge = %s WHERE id = %s",
                (name, email, profile_pic, certification_badge, user_id)
            )
            
            # Update session variables
            session["user_name"] = name
            
            flash("Profile updated successfully!", "success")
            db.close()
            return redirect(url_for('auth.profile'))
            
        # Fetch user info
        user_query = "SELECT id, name, email, role, profile_pic, certification_badge, created_at FROM users WHERE id = %s"
        user = db.fetch_one(user_query, (user_id,))
        
        # Fetch user's order history using the orders table schema
        orders_query = """
            SELECT id, total_amount, order_status, created_at 
            FROM orders WHERE user_id = %s ORDER BY created_at DESC
        """
        orders = db.fetch_all(orders_query, (user_id,))
        db.close()
        
        return render_template('profile.html', user=user, orders=orders)

    def deactivate_account(self):
        """Deactivate the logged in user account."""
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))
            
        user_id = session['user_id']
        db = Database()
        db.execute("UPDATE users SET is_active = 0 WHERE id = %s", (user_id,))
        db.close()
        
        session.clear()
        flash("Your account has been deactivated successfully.", "info")
        return redirect(url_for('auth.login'))

    def delete_account(self):
        """Delete the logged in user account permanently."""
        if 'user_id' not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for('auth.login'))
            
        user_id = session['user_id']
        db = Database()
        db.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db.close()
        
        session.clear()
        flash("Your account has been deleted permanently.", "info")
        return redirect(url_for('auth.login'))

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
        # Security check to ensure only merchants see this
        if session.get("role") != "merchant":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("auth.home"))
        
        merchant_id = session.get("user_id")
        db = Database()
        
        # Fetch merchant user info (profile pic, certificate status)
        user = db.fetch_one("SELECT name, email, profile_pic, certification_badge FROM users WHERE id = %s", (merchant_id,))
        
        # Fetch herbs for the current merchant
        herbs = db.fetch_all("SELECT * FROM herbs WHERE merchant_id = %s", (merchant_id,))
        
        # Fetch top selling herbs for this merchant
        chart_query = """
            SELECT h.common_name, CAST(SUM(oi.quantity) AS UNSIGNED) as total_sold
            FROM order_items oi
            JOIN herbs h ON oi.herb_id = h.id
            WHERE h.merchant_id = %s
            GROUP BY oi.herb_id
            ORDER BY total_sold DESC
        """
        top_selling = db.fetch_all(chart_query, (merchant_id,))
        
        db.close()
        
        # Identify low stock items (stock <= 5)
        low_stock_herbs = [h for h in herbs if h["stock_quantity"] <= 5]
        
        # Fetch orders for the current merchant (uses corrected query)
        orders = self.order_model.get_merchant_orders(merchant_id)
        return render_template("merchant_dashboard.html", herbs=herbs, orders=orders, user=user, top_selling=top_selling, low_stock_herbs=low_stock_herbs)

    # ── Google OAuth Login ─────────────────────────────────────
    def google_login(self):
        credential = request.form.get("credential")
        if not credential:
            # Check if it is a mock request (JSON payload or query parameter)
            credential = request.json.get("credential") if request.is_json else None
        
        email = None
        name = None

        if credential == "mock_google_token":
            # Dev mock fallback login
            email = "google_mock_user@example.com"
            name = "Google Mock User"
        elif credential:
            # CSRF Verification
            csrf_cookie = request.cookies.get("g_csrf_token")
            csrf_body = request.form.get("g_csrf_token")
            if csrf_body and csrf_cookie != csrf_body:
                flash("CSRF verification failed for Google Sign-In.", "danger")
                return redirect(url_for("auth.login"))

            # Real Google Sign-in verification
            try:
                # Query Google tokeninfo API to verify JWT
                url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
                with urllib.request.urlopen(url) as response:
                    token_info = json.loads(response.read().decode())
                    
                    # Validate Client ID configuration and match
                    client_id = config.GOOGLE_CLIENT_ID
                    if not client_id:
                        flash("Google login is not configured on this server.", "danger")
                        return redirect(url_for("auth.login"))
                    
                    if token_info.get("aud") != client_id.strip():
                        flash("Google authentication mismatch (Client ID client verification failed).", "danger")
                        return redirect(url_for("auth.login"))
                    
                    # Validate that email is verified by Google
                    if not token_info.get("email_verified"):
                        flash("Google email is not verified.", "danger")
                        return redirect(url_for("auth.login"))
                    
                    email = token_info.get("email")
                    name = token_info.get("name", email.split('@')[0] if email else "Google User")
            except Exception as e:
                print(f"Google Token Verification Failed: {e}")
                flash("Failed to verify Google credentials. Please try again.", "danger")
                return redirect(url_for("auth.login"))
        
        if not email:
            flash("Invalid Google Sign-In attempt.", "danger")
            return redirect(url_for("auth.login"))

        # Log user in or register automatically
        db = Database()
        user_data = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
        
        if not user_data:
            # Register new Google user
            # Password can be a random secure hash
            random_pw = str(uuid.uuid4())
            hashed_pw = generate_password_hash(random_pw)
            db.execute(
                "INSERT INTO users (name, email, password, role, is_active) VALUES (%s, %s, %s, %s, 1)",
                (name, email, hashed_pw, "user")
            )
            user_data = db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
            print(f"Registered new Google OAuth user: {email}")
        else:
            if user_data.get("is_active") == 0:
                db.close()
                flash("This account has been deactivated. Please contact support to reactivate it.", "danger")
                return redirect(url_for("auth.login"))

        db.close()

        # Set session variables
        session["user_id"]   = user_data["id"]
        session["user_name"] = user_data["name"]
        session["role"]      = user_data["role"]

        # Dynamic backend routing based on role matrix
        target_route = self._get_redirect_route(user_data["role"])
        return self.flash_and_redirect(
            "Logged in successfully via Google!", "success", target_route
        )

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

            # Generate numeric 6-digit OTP
            otp = f"{random.randint(100000, 999999)}"
            # Set expiry (now + 10 mins)
            expiry = datetime.now() + timedelta(minutes=10)

            # Save to users database
            db.execute(
                "UPDATE users SET otp_code = %s, otp_expiry = %s WHERE id = %s",
                (otp, expiry.strftime('%Y-%m-%d %H:%M:%S'), user["id"])
            )
            db.close()

            # Try sending via real email first, fall back to terminal
            email_sent = send_otp_email(email, otp, expiry.strftime('%I:%M:%S %p'))

            if email_sent:
                flash("A 6-digit verification code has been sent to your email inbox.", "success")
            else:
                # Fallback: print to terminal for local dev/grading
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

            # Check expiry
            # Parse database timestamp if it comes as datetime or string
            expiry = user.get("otp_expiry")
            if isinstance(expiry, str):
                expiry = datetime.strptime(expiry, '%Y-%m-%d %H:%M:%S')
            
            if expiry and expiry < datetime.now():
                db.close()
                flash("OTP code has expired. Please request a new one.", "danger")
                return redirect(url_for("auth.forgot_password"))

            db.close()
            # Mark OTP as verified for this email in session
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

            # Update password
            hashed_pw = generate_password_hash(password)
            db = Database()
            db.execute(
                "UPDATE users SET password = %s, otp_code = NULL, otp_expiry = NULL WHERE email = %s",
                (hashed_pw, email)
            )
            db.close()

            # Clear verification from session
            session.pop("otp_verified_email", None)
            flash("Your password has been reset successfully! You can now log in.", "success")
            return redirect(url_for("auth.login"))

        return render_template("reset_password.html")
