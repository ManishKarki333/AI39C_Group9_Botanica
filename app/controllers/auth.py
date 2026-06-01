from flask import render_template, redirect, url_for, session, flash, request
from app.controllers.base_controller import BaseController
from app.models.database import Database
from app.models.user_model import User

class AuthController(BaseController):
    def __init__(self):
        self.user_model = User()
        
    def home(self): 
        return render_template("home.html")

    def _get_redirect_route(self, role):
        """Helper method to determine home portal based on user roles."""
        if role == "admin":
            return "auth.dashboard"
        elif role == "merchant":
            return "auth.merchant_dashboard"
        else:
            # Default customer/buyer landing page
            return "auth.home"

    def login(self):
        # 1. If already logged in, route to their correct dashboard environment
        if self.is_logged_in():
            current_role = session.get("role", "customer")
            return redirect(url_for(self._get_redirect_route(current_role)))

        if request.method == "POST":
            # Extract and strip whitespace from email to prevent login errors
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")

            if not email or not password:
                flash("Email and password are required.", "danger")
                return render_template("login.html")

            # Use the User model to find the user
            user_data = self.user_model.find_by("email", email)

            if user_data:
                # Build a User object from database data
                user = User.from_db(user_data)
                
                if user.check_password(password):
                    # Establish session credentials
                    session["user_id"] = user_data["id"]
                    session["user_name"] = user_data["name"]
                    session["role"] = user_data["role"]
                    
                    # Dynamic backend routing based on database role matrix
                    target_route = self._get_redirect_route(user_data["role"])
                    return self.flash_and_redirect(
                        "Login successful!", "success", target_route
                    )

            flash("Invalid email or password.", "danger")
        return render_template("login.html")


    def register(self):
        # Route safely if user hits registration route while authenticated
        if self.is_logged_in():
            current_role = session.get("role", "customer")
            return redirect(url_for(self._get_redirect_route(current_role)))

        if request.method == "POST":
            # Standardized and cleaned form data extraction
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            password = request.form.get("password", "")
            
            # Dynamically capture role from the signup page with strict fallback
            role = request.form.get("role", "customer")
            if role not in ["customer", "merchant"]:
                role = "customer" # Force fallback to lowest privilege

            # Validation
            if not name or not email or not password:
                flash("All fields are required.", "danger")
                return render_template("register.html")

            if len(name) > 100:
                flash("Name must be under 100 characters.", "danger")
                return render_template("register.html")

            if len(password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("register.html")

            # Create a new User object with assigned role
            new_user = User(name=name, email=email, password=password, role=role)

            if new_user.email_exists():
                flash("Email already exists.", "danger")
                return redirect(url_for("auth.register"))

            # Save to database
            new_user.save()
            return self.flash_and_redirect(
                "Registration successful! Please login.", "success", "auth.login"
            )

        return render_template("register.html")


    def merchant_dashboard(self):
        # Ensure role is validated
        if not self.is_logged_in() or session.get("role") != "merchant":
            flash("Unauthorized access.", "danger")
            return redirect(url_for("auth.login"))
        
        # ... security checks ...
        db = Database()
        # Ensure 'merchant_id' column exists and matches your table
        query = "SELECT * FROM herbs" 
        merchant_herbs = db.fetch_all(query)
        db.close()
        return render_template("merchant_dashboard.html", herbs=merchant_herbs)

    def logout(self):
        session.clear()
        return self.flash_and_redirect("You have been logged out.", "success", "auth.login")
    
    def about(self):
        return render_template("about.html")
    
    def contact(self):
        return render_template("contact.html")
    
    