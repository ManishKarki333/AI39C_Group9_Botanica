from app import create_app
from app.models.database import Database

app = create_app()
with app.app_context():
    db = Database()
    users = db.fetch_all("SELECT id, name, email, role FROM users")
    db.close()
    for u in users:
        print(u)
