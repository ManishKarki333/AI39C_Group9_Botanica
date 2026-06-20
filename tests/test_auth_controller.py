import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from datetime import datetime, timedelta
from app.controllers.auth import AuthController


#  FLASK ENVIRONMENT MOCK HELPER
def make_test_app():
    """
    Builds an isolated headless Flask application instance.
    Defines endpoints required for url_for() redirections inside AuthController.
    """
    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    app.config['GOOGLE_CLIENT_ID'] = "mock-google-id.apps.googleusercontent.com"

    bp = Blueprint("auth", __name__)
    bp.route("/", endpoint="home")(lambda: "home")
    bp.route("/login", endpoint="login")(lambda: "login")
    bp.route("/register", endpoint="register")(lambda: "register")
    bp.route("/profile", endpoint="profile")(lambda: "profile")
    bp.route("/merchant/dashboard", endpoint="merchant_dashboard")(lambda: "merchant_dashboard")
    bp.route("/verify-otp", endpoint="verify_otp")(lambda: "verify_otp")
    bp.route("/reset-password", endpoint="reset_password")(lambda: "reset_password")
    app.register_blueprint(bp)

    admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
    admin_bp.route("/dashboard", endpoint="dashboard")(lambda: "admin_dashboard")
    app.register_blueprint(admin_bp)

    return app


#  TEST CASES: REGISTRATION LAYER
class TestRegister(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        self.controller.user_model = MagicMock()

    @patch("app.controllers.auth.render_template")
    def test_register_get_shows_form(self, mock_render):
        """Visiting register with GET should show the register form."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(method="GET"):
            result = self.controller.register()
            self.assertEqual(result, "register_page")
            mock_render.assert_called_once_with("register.html")

    @patch("app.controllers.auth.render_template")
    def test_register_missing_fields_is_rejected(self, mock_render):
        """If any field is empty, registration is refused with a message."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(
            method="POST", data={"name": "", "email": "", "password": ""}
        ):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "All fields are required."), flashes)

    @patch("app.controllers.auth.render_template")
    def test_register_invalid_email_format_is_rejected(self, mock_render):
        """Providing an incorrectly structured email throws a format message."""
        mock_render.return_value = "register_page"
        with self.app.test_request_context(
            method="POST", data={"name": "Alice", "email": "bademail.com", "password": "password123"}
        ):
            self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Please enter a valid email address."), flashes)

    def test_register_duplicate_email_is_rejected(self):
        """If the email already exists, registration is refused."""
        self.controller.user_model.find_by.return_value = {"id": 1, "email": "taken@example.com"}

        with self.app.test_request_context(
            method="POST",
            data={"name": "Bob", "email": "taken@example.com", "password": "secret123", "role": "user"},
        ):
            response = self.controller.register()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("warning", "Email already registered. Please log in."), flashes)
            self.assertEqual(response.status_code, 302)


#  TEST CASES: LOGIN LAYER
class TestLogin(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        self.controller.user_model = MagicMock()

    @patch("app.controllers.auth.render_template")
    def test_login_get_shows_form(self, mock_render):
        """Visiting login with GET should show the login form."""
        mock_render.return_value = "login_page"
        with self.app.test_request_context(method="GET"):
            result = self.controller.login()
            self.assertEqual(result, "login_page")

    @patch("app.controllers.auth.render_template")
    def test_login_missing_fields_is_rejected(self, mock_render):
        """Empty fields flash an entry warning."""
        mock_render.return_value = "login_page"
        with self.app.test_request_context(method="POST", data={"email": "", "password": ""}):
            self.controller.login()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "Email and password are required."), flashes)

    @patch("app.controllers.auth.User.from_db")
    def test_login_deactivated_user_is_rejected(self, mock_from_db):
        """Accounts flagged with is_active = 0 remain blocked on login."""
        self.controller.user_model.find_by.return_value = {
            "id": 8, "name": "Arbin", "email": "arbin@example.com", "role": "merchant", "is_active": 0
        }
        fake_user = MagicMock()
        fake_user.check_password.return_value = True
        mock_from_db.return_value = fake_user

        with self.app.test_request_context(
            method="POST", data={"email": "arbin@example.com", "password": "password123"}
        ):
            self.controller.login()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "This account has been deactivated. Please contact support to reactivate it."), flashes)
            self.assertNotIn("user_id", session)

    @patch("app.controllers.auth.User.from_db")
    def test_login_success_sets_session_and_redirects(self, mock_from_db):
        """Successful validation assigns server context identities."""
        self.controller.user_model.find_by.return_value = {
            "id": 3, "name": "User Three", "email": "three@example.com", "role": "user", "is_active": 1
        }
        fake_user = MagicMock()
        fake_user.check_password.return_value = True
        mock_from_db.return_value = fake_user

        with self.app.test_request_context(
            method="POST", data={"email": "three@example.com", "password": "password123"}
        ):
            response = self.controller.login()
            self.assertEqual(session["user_id"], 3)
            self.assertEqual(session["role"], "user")
            self.assertEqual(response.status_code, 302)


#  TEST CASES: ACCOUNT LIFECYCLE MANAGEMENT LAYER
class TestAccountLifecycle(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()

    @patch("app.controllers.auth.Database")
    def test_deactivate_account(self, mock_db_class):
        """Deactivating switches database status bits and purges active cookies."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        with self.app.test_request_context():
            session["user_id"] = 5
            response = self.controller.deactivate_account()

            mock_db.execute.assert_called_with("UPDATE users SET is_active = 0 WHERE id = %s", (5,))
            self.assertNotIn("user_id", session)
            self.assertEqual(response.status_code, 302)

    @patch("app.controllers.auth.Database")
    def test_delete_account(self, mock_db_class):
        """Deleting triggers permanent raw key row destruction queries."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        with self.app.test_request_context():
            session["user_id"] = 5
            response = self.controller.delete_account()

            mock_db.execute.assert_called_with("DELETE FROM users WHERE id = %s", (5,))
            self.assertNotIn("user_id", session)


#  TEST CASES: PASSWORDS & SECURITY TOKENS (OTP)
class TestOTPValidation(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()

    @patch("app.controllers.auth.Database")
    def test_verify_otp_success(self, mock_db_class):
        """Providing a valid, unexpired token sets authorization scopes."""
        mock_db = MagicMock()
        future_expiry = datetime.now() + timedelta(minutes=10)
        mock_db.fetch_one.return_value = {"id": 1, "otp_code": "123456", "otp_expiry": future_expiry}
        mock_db_class.return_value = mock_db

        with self.app.test_request_context(method="POST", data={"otp": "123456"}):
            session["otp_reset_email"] = "test@example.com"
            response = self.controller.verify_otp()

            self.assertEqual(session["otp_verified_email"], "test@example.com")
            self.assertEqual(response.status_code, 302)

    @patch("app.controllers.auth.Database")
    def test_verify_otp_expired(self, mock_db_class):
        """Providing an expired token causes validation rejection."""
        mock_db = MagicMock()
        past_expiry = datetime.now() - timedelta(minutes=5)
        mock_db.fetch_one.return_value = {"id": 1, "otp_code": "123456", "otp_expiry": past_expiry}
        mock_db_class.return_value = mock_db

        with self.app.test_request_context(method="POST", data={"otp": "123456"}):
            session["otp_reset_email"] = "test@example.com"
            self.controller.verify_otp()
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("danger", "OTP code has expired. Please request a new one."), flashes)


if __name__ == "__main__":
    unittest.main()