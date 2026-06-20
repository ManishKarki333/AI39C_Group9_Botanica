import unittest
from unittest.mock import MagicMock, patch, ANY
from flask import Flask, session
from app.controllers.shop_controller import ShopController
from datetime import datetime


class TestShopController(unittest.TestCase):

    def setUp(self):
        """Set up a clean Flask application context for testing sessions and requests."""
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'test_secret_key'
        self.app.config['TESTING'] = True
        self.controller = ShopController()

        # Patch url_for globally across all tests to prevent Blueprint BuildErrors
        self.url_for_patcher = patch('app.controllers.shop_controller.url_for', return_value='/mock-url')
        self.mock_url_for = self.url_for_patcher.start()

    def tearDown(self):
        """Stop the global patches to keep the environment clean."""
        self.url_for_patcher.stop()

    # =========================================================================
    # UPPER-HALF METHODS (STOREFRONT, LIBRARY, REVIEWS, & VENDOR INVENTORY)
    # =========================================================================

    @patch('app.controllers.shop_controller.Database')
    @patch('app.controllers.shop_controller.render_template')
    def test_shop_view_with_filters(self, mock_render, mock_db_class):
        """Test synchronous store grid with search keywords and active category filters."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_all.side_effect = [[{"id": 1}], [{"id": 10, "name": "Roots"}]]

        with self.app.test_request_context('/shop?search=Ginseng&category=Energy'):
            self.controller.shop()
            
            expected_query = "SELECT * FROM herbs WHERE 1=1 AND (common_name LIKE %s OR scientific_name LIKE %s) AND benefit_category = %s"
            mock_db.fetch_all.assert_any_call(expected_query, ('%Ginseng%', '%Ginseng%', 'Energy'))
            mock_db.close.assert_called_once()

    @patch('app.controllers.shop_controller.Database')
    @patch('app.controllers.shop_controller.render_template')
    def test_herb_library_deduplication(self, mock_render, mock_db_class):
        """Verify the academic library strictly unique-deduplicates overlapping merchant records."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        
        mock_db.fetch_all.side_effect = [
            [
                {"scientific_name": "Mentha piperita", "common_name": "Mint A"},
                {"scientific_name": "Mentha piperita ", "common_name": "Mint B"},
                {"scientific_name": None, "common_name": "Unique Herb"}
            ],
            [{"name": "Digestive"}]
        ]

        with self.app.test_request_context('/library'):
            self.controller.herb_library()
            
            render_args, render_kwargs = mock_render.call_args
            rendered_herbs = render_kwargs['herbs']
            
            self.assertEqual(len(rendered_herbs), 2)
            self.assertEqual(rendered_herbs[0]['common_name'], 'Mint A')
            self.assertEqual(rendered_herbs[1]['common_name'], 'Unique Herb')

    @patch('app.controllers.shop_controller.Database')
    @patch('app.controllers.shop_controller.render_template')
    def test_herb_details_calculates_average_rating(self, mock_render, mock_db_class):
        """Test dynamic calculation and math rounding for user evaluation averages."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {"id": 5, "common_name": "Echinacea"}
        mock_db.fetch_all.return_value = [{"rating": 4}, {"rating": 5}, {"rating": 4}]

        with self.app.test_request_context('/herb/5'):
            self.controller.herb_details(5)
            
            render_kwargs = mock_render.call_args[1]
            self.assertEqual(render_kwargs['average_rating'], 4.3)
            self.assertEqual(render_kwargs['total_reviews'], 3)

    @patch('app.controllers.shop_controller.Database')
    def test_add_review_authenticated_success(self, mock_db_class):
        """Test successfully inserting user text commentary and numeric rating."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        with self.app.test_request_context('/herb/5/review', method='POST', data={'rating': '5', 'comment': 'Excellent quality!'}):
            session['user_id'] = 42
            self.controller.add_review(5)
            
            mock_db.execute.assert_called_with(
                ANY, (5, 42, 5, 'Excellent quality!', None)
            )
            mock_db.commit.assert_called_once()

    @patch('app.controllers.shop_controller.Database')
    @patch('app.controllers.shop_controller.os.path.exists')
    @patch('app.controllers.shop_controller.os.remove')
    def test_delete_review_author_permissions(self, mock_remove, mock_exists, mock_db_class):
        """Ensure review file-cleanup actions fire when author deletes content."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {'id': 1, 'user_id': 10, 'herb_id': 2, 'image_url': '/static/uploads/Herbs Picture/review_img.jpg'}
        mock_exists.return_value = True

        with self.app.test_request_context('/review/1/delete'):
            session['user_id'] = 10
            session['role'] = 'buyer'
            self.controller.delete_review(1)
            
            mock_remove.assert_called_once()
            mock_db.execute.assert_called_with("DELETE FROM reviews WHERE id = %s", (1,))

    @patch('app.controllers.shop_controller.Database')
    def test_add_product_merchant_success(self, mock_db_class):
        """Verify merchant catalog additions process inserts along with price history points."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {"id": 50}

        product_form = {
            'common_name': 'Lavender', 'scientific_name': 'Lavandula', 'description': 'Calming',
            'price': '15.00', 'benefit_category': 'Relax', 'stock_quantity': '20', 'whatsapp_number': '9800000000'
        }

        with self.app.test_request_context('/product/add', method='POST', data=product_form):
            session['user_id'] = 3
            session['role'] = 'merchant'
            self.controller.add_product()
            
            mock_db.execute.assert_any_call(
                "INSERT INTO herbs \n                        (common_name, scientific_name, description, price, benefit_category, stock_quantity, image_url, merchant_id, whatsapp_number, reference_url, qr_payment_type, qr_code_url) \n                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                ANY
            )
            mock_db.execute.assert_any_call("INSERT INTO price_history (herb_id, price) VALUES (%s, %s)", (50, '15.00'))

    @patch('app.controllers.shop_controller.Database')
    def test_update_product_price_change_triggers_history(self, mock_db_class):
        """Ensure modification logs catch vendor price deviations."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {"price": 10.00, "merchant_id": 3, "qr_code_url": None, "image_url": None}

        update_form = {
            'common_name': 'Lavender', 'scientific_name': 'Lavandula',
            'price': '12.50', 'stock_quantity': '20', 'whatsapp_number': '9800000000'
        }

        with self.app.test_request_context('/product/50/update', method='POST', data=update_form):
            session['user_id'] = 3
            session['role'] = 'merchant'
            self.controller.update_product(50)
            
            mock_db.execute.assert_any_call("INSERT INTO price_history (herb_id, price) VALUES (%s, %s)", (50, 12.50))

    # =========================================================================
    # LOWER-HALF METHODS (CART, CHECKOUT, TRACKING, AND ADMINISTRATIVE REPORTS)
    # =========================================================================

    @patch('app.controllers.shop_controller.Database')
    def test_add_to_cart_multi_merchant_guardrail(self, mock_db_class):
        """Ensure users cannot mix different merchant products inside the same cart session."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {"id": 12, "common_name": "Peppermint", "scientific_name": "Mentha", "price": 5.0, "merchant_id": 99}

        with self.app.test_request_context('/add-to-cart', method='POST', json={'herb_id': 12}):
            session['cart'] = [{'id': 5, 'merchant_id': 1, 'quantity': 1}]
            response, status_code = self.controller.add_to_cart()
            
            self.assertEqual(status_code, 400)
            self.assertIn('already contains items from another merchant', response.get_json()['message'])

    @patch('app.controllers.shop_controller.Database')
    def test_api_price_history_formatting(self, mock_db_class):
        """Verify timestamp strings cleanly map json structural configurations across APIs."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {"merchant_id": 2, "price": 100.0}
        mock_db.fetch_all.return_value = [{"price": 100.0, "created_at": datetime(2026, 5, 20, 12, 0, 0)}]

        with self.app.test_request_context('/api/price-history/1'):
            session['user_id'] = 2
            session['role'] = 'merchant'
            response = self.controller.api_price_history(1)
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()['history'][0]['date'], '2026-05-20 12:00:00')

    @patch('app.controllers.shop_controller.Database')
    def test_cancel_order_unauthorized_state(self, mock_db_class):
        """Ensure users cannot delete orders once they transition past processing statuses."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db
        mock_db.fetch_one.return_value = {'id': 101, 'order_status': 'Shipped', 'user_id': 14}

        with self.app.test_request_context('/order/101/cancel', method='POST', data={'cancellation_reason': 'Changed mind'}):
            session['user_id'] = 14
            self.controller.cancel_order(101)
            mock_db.execute.assert_not_called()

    @patch('app.controllers.shop_controller.Database')
    def test_report_product_submission(self, mock_db_class):
        """Test reporting an item flags its index tracking entry inside administration portals."""
        mock_db = MagicMock()
        mock_db_class.return_value = mock_db

        with self.app.test_request_context('/product/8/report', method='POST', data={'reason': 'Misleading Label', 'description': 'Not organic'}):
            session['user_id'] = 5
            self.controller.report_product(8)
            
            mock_db.execute.assert_called_with(
                "INSERT INTO reports (user_id, target_type, target_id, reason, description, status) VALUES (%s, %s, %s, %s, %s, 'pending')",
                (5, 'product', 8, 'Misleading Label', 'Not organic')
            )


if __name__ == '__main__':
    unittest.main()