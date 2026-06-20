from flask import Blueprint
from app.controllers.admin_controller import AdminController
from app.auth import admin_required


class AdminRoutes:
    def __init__(self):
        self.bp = Blueprint("admin", __name__)
        self.controller = AdminController()

    def register(self):
        # 1. Overview Dashboard
        self.bp.route("/dashboard", methods=["GET"])(
            admin_required(self.controller.dashboard)
        )

        # 2. User/Merchant Management
        self.bp.route("/users", methods=["GET"])(
            admin_required(self.controller.users_list)
        )
        self.bp.route("/user/toggle_status/<int:user_id>", methods=["POST"])(
            admin_required(self.controller.toggle_user_status)
        )
        self.bp.route("/user/delete/<int:user_id>", methods=["POST"])(
            admin_required(self.controller.delete_user_account)
        )
        self.bp.route("/merchant/<int:merchant_id>", methods=["GET"])(
            admin_required(self.controller.merchant_detail)
        )

        # 3. Product Management
        self.bp.route("/products", methods=["GET"])(
            admin_required(self.controller.products_list)
        )
        self.bp.route("/product/delete/<int:product_id>", methods=["POST"])(
            admin_required(self.controller.delete_product)
        )

        # 4. Category Management
        self.bp.route("/categories", methods=["GET", "POST"])(
            admin_required(self.controller.categories_list)
        )
        self.bp.route("/categories/add", methods=["POST"])(
            admin_required(self.controller.add_category)
        )
        self.bp.route("/categories/edit/<int:cat_id>", methods=["POST"])(
            admin_required(self.controller.edit_category)
        )
        self.bp.route("/categories/delete/<int:cat_id>", methods=["POST"])(
            admin_required(self.controller.delete_category)
        )

        # 5. Reports & Moderation
        self.bp.route("/reports", methods=["GET"])(
            admin_required(self.controller.reports_list)
        )
        self.bp.route("/reports/resolve/<int:report_id>", methods=["POST"])(
            admin_required(self.controller.resolve_report)
        )

        return self.bp
