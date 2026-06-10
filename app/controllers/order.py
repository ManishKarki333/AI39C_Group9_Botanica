from flask import render_template
from app.models.database import Database

class OrderController:
    def order_status(self):
        orders = []
        return render_template('order_status.html', orders=orders)
