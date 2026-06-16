from app import create_app
from app.models.database import Database
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    db = Database()
    new_hash = generate_password_hash("password123")
    # Let's change the password of user with id=8 (Arbin)
    db.execute("UPDATE users SET password = %s WHERE id = 8", (new_hash,))
    # Let's also check if user 3 has a password we can use to place orders:
    db.execute("UPDATE users SET password = %s WHERE id = 3", (new_hash,))
    if hasattr(db, 'commit'):
        db.commit()
    db.close()
    print("Passwords updated successfully!")
