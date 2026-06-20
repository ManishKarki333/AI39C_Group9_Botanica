import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, get_flashed_messages
from app.controllers.admin_controller import AdminController # Corrected path

def make_test_app():
    app = Flask(__name__)
    app.secret_key = "admin-test-secret-key"
    bp = Blueprint("admin", __name__)
    bp.route("/dashboard", endpoint="dashboard")(lambda: "dashboard")
    app.register_blueprint(bp)
    return app

class TestAdminController(unittest.TestCase):
    def setUp(self):
        self.app = make_test_app()
        self.controller = AdminController()

    @patch("app.controllers.admin_controller.Database") # Corrected path
    @patch("app.controllers.admin_controller.render_template") # Corrected path
    def test_dashboard_metrics_and_lists_render(self, mock_render, mock_db_class):
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_render.return_value = "admin_dashboard_rendered"

        mock_db.fetch_one.side_effect = [
            {"count": 10}, {"count": 5}, {"count": 25}, {"count": 14},
            {"count": 1}, {"count": 2}, {"count": 50}, {"total": 1250.50}
        ]
        mock_db.fetch_all.side_effect = [
            [{"id": 1, "name": "Alice"}],
            [{"id": 101, "common_name": "Chamomile", "merchant_name": "Bob"}],
            [{"id": 1, "name": "Relaxation"}],
            [{"id": 9, "target_type": "product", "reporter_name": "Alice"}],
            [{"id": 500, "total_amount": 50.00, "customer_name": "Alice"}]
        ]

        with self.app.test_request_context(method="GET"):
            result = self.controller.dashboard()
            self.assertEqual(result, "admin_dashboard_rendered")

    @patch("app.controllers.admin_controller.Database") # Corrected path
    def test_toggle_user_status_suspends_active_user(self, mock_db_class):
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {"is_active": 1, "name": "John Doe"}

        with self.app.test_request_context(method="POST"):
            response = self.controller.toggle_user_status(user_id=5)
            mock_db.execute.assert_called_with("UPDATE users SET is_active = %s WHERE id = %s", (0, 5))
            self.assertEqual(response.status_code, 302)

    @patch("app.controllers.admin_controller.os.path.exists") # Corrected path
    @patch("app.controllers.admin_controller.os.remove") # Corrected path
    @patch("app.controllers.admin_controller.Database") # Corrected path
    def test_delete_user_account_removes_merchant_images(self, mock_db_class, mock_remove, mock_exists):
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {"name": "Merchant Bob"}
        mock_db.fetch_all.return_value = [{"image_url": "/static/uploads/mint.png"}]
        mock_exists.return_value = True

        with self.app.test_request_context(method="POST"):
            self.controller.delete_user_account(user_id=12)
            mock_remove.assert_called_once()
            mock_db.execute.assert_called_with("DELETE FROM users WHERE id = %s", (12,))

    @patch("app.controllers.admin_controller.Database") # Corrected path
    def test_add_category_success(self, mock_db_class):
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        with self.app.test_request_context(method="POST", data={"name": "Medicinal Roots"}):
            self.controller.add_category()
            mock_db.execute.assert_called_with("INSERT INTO categories (name) VALUES (%s)", ("Medicinal Roots",))

    @patch("app.controllers.admin_controller.Database") # Corrected path
    def test_add_category_empty_is_rejected(self, mock_db_class):
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        with self.app.test_request_context(method="POST", data={"name": "   "}):
            self.controller.add_category()
            mock_db.execute.assert_not_called()

    @patch("app.controllers.admin_controller.Database") # Corrected path
    def test_delete_category_blocked_by_active_dependencies(self, mock_db_class):
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.side_effect = [{"name": "Teas"}, {"count": 3}]

        with self.app.test_request_context(method="POST"):
            self.controller.delete_category(cat_id=2)
            mock_db.execute.assert_not_called()

    @patch("app.controllers.admin_controller.Database") # Corrected path
    def test_resolve_report(self, mock_db_class):
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        with self.app.test_request_context(method="POST"):
            self.controller.resolve_report(report_id=42)
            mock_db.execute.assert_called_with("UPDATE reports SET status = 'resolved' WHERE id = %s", (42,))

if __name__ == "__main__":
    unittest.main()