from flask import Blueprint, render_template

order_bp = Blueprint('order', __name__)

@order_bp.route('/order_status')
def order_status():
    # orders=[] for now since we are only doing frontend
    return render_template('order_status.html', orders=[])
