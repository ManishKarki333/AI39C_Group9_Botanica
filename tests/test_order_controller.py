import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, session
# 1. Bypassing the @merchant_required decorator by mocking it BEFORE importing the controller
import sys
from unittest.mock import Mock

def mock_decorator(f):
    return f  # Simply passes the original function through untouched

# Fake the auth module's decorator so it does nothing during test runs
sys.modules['app.auth'] = Mock(merchant_required=mock_decorator)

# Now it is completely safe to import the controller without decorator interference
from app.controllers.order_controller import OrderController


class TestOrderController(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "botanica-test-secret"
        self.controller = OrderController()

    # TESTS FOR: update_status

    def test_update_status_success(self):
        # Arrange
        self.controller.order_model.update_status = MagicMock(return_value=True)

        # Act
        with self.app.test_request_context(method="POST", data={"order_status": "Shipped"}):
            session["user_id"] = 10  # Setting session safely within context
            response, status_code = self.controller.update_status(order_id=101)

            # Assert
            self.assertEqual(status_code, 200)
            self.assertEqual(response.json["status"], "success")
            self.assertIn("updated to Shipped", response.json["message"])
            self.controller.order_model.update_status.assert_called_once_with(101, "Shipped", 10)

    def test_update_status_invalid_or_missing_status(self):
        # Act & Assert with invalid status string
        with self.app.test_request_context(method="POST", data={"order_status": "Destroyed"}):
            response, status_code = self.controller.update_status(order_id=101)
            self.assertEqual(status_code, 400)
            self.assertEqual(response.json["message"], "Invalid status selection.")

    def test_update_status_unauthorized_or_not_found(self):
        # Arrange
        self.controller.order_model.update_status = MagicMock(return_value=False)

        # Act
        with self.app.test_request_context(method="POST", data={"order_status": "Processing"}):
            session["user_id"] = 10
            response, status_code = self.controller.update_status(order_id=101)

            # Assert
            self.assertEqual(status_code, 403)
            self.assertEqual(response.json["message"], "Unauthorized access or order not found.")

    def test_update_status_system_error(self):
        # Arrange
        self.controller.order_model.update_status = MagicMock(side_effect=Exception("Database crash"))

        # Act
        with self.app.test_request_context(method="POST", data={"order_status": "Processing"}):
            session["user_id"] = 10
            response, status_code = self.controller.update_status(order_id=101)

            # Assert
            self.assertEqual(status_code, 500)
            self.assertEqual(response.json["message"], "A system error occurred.")


    # TESTS FOR: update_payment_status

    def test_update_payment_status_invalid_selection(self):
        with self.app.test_request_context(method="POST", data={"payment_status": "Pending_Refund"}):
            response, status_code = self.controller.update_payment_status(order_id=101)
            self.assertEqual(status_code, 400)
            self.assertEqual(response.json["message"], "Invalid payment status selection.")

    @patch("app.models.database.Database")
    def test_update_payment_status_unauthorized_order(self, mock_db_class):
        # Arrange
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = None  # Mocking no matching order found

        # Act
        with self.app.test_request_context(method="POST", data={"payment_status": "Paid"}):
            session["user_id"] = 10
            response, status_code = self.controller.update_payment_status(order_id=101)

            # Assert
            self.assertEqual(status_code, 403)
            mock_db.close.assert_called_once()

    @patch("app.models.database.Database")
    def test_update_payment_status_paid_triggers_stock_reduction(self, mock_db_class):
        # Arrange
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        # Simulating current DB state transitions
        mock_db.fetch_one.return_value = {"id": 101, "payment_status": "Unpaid"}
        mock_db.fetch_all.return_value = [
            {"herb_id": 1, "quantity": 2},
            {"herb_id": 5, "quantity": 1}
        ]

        # Act
        with self.app.test_request_context(method="POST", data={"payment_status": "Paid"}):
            session["user_id"] = 10
            response, status_code = self.controller.update_payment_status(order_id=101)

            # Assert
            self.assertEqual(status_code, 200)
            # Verify the general update status execution
            mock_db.execute.assert_any_call("UPDATE orders SET payment_status = %s WHERE id = %s", ("Paid", 101))
            self.assertEqual(mock_db.execute.call_count, 3)  # 2 items updates + 1 order status update
            mock_db.close.assert_called_once()

    @patch("app.models.database.Database")
    def test_update_payment_status_already_paid_skips_stock_reduction(self, mock_db_class):
        # Arrange
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {"id": 101, "payment_status": "Paid"}

        # Act
        with self.app.test_request_context(method="POST", data={"payment_status": "Paid"}):
            session["user_id"] = 10
            response, status_code = self.controller.update_payment_status(order_id=101)

            # Assert
            self.assertEqual(status_code, 200)
            mock_db.fetch_all.assert_not_called()  # Stock collection shouldn't run if already paid
            mock_db.execute.assert_called_once_with("UPDATE orders SET payment_status = %s WHERE id = %s", ("Paid", 101))


if __name__ == "__main__":
    unittest.main()