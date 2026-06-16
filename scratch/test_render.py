from app import create_app
from app.models.database import Database
from app.models.order_model import Order

app = create_app()
with app.app_context():
    merchant_id = 8
    db = Database()
    order_model = Order()
    orders = order_model.get_merchant_orders(merchant_id)
    db.close()
    
    print("ORDER IDS IN DB QUERY:", [o['id'] for o in orders])
    print("ORDER DATA:")
    for o in orders:
        print(f"ID: {o['id']}, User: {o['user_id']}, Window: {o['delivery_window']}, Created: {o['created_at']}")
