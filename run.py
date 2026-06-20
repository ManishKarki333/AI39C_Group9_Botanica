from app import create_app
from app.models.database import Database
from config import SECRET_KEY

app = create_app()

if __name__ == '__main__':
    Database.create_tables()
    app.run(debug=True)