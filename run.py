from app import create_app
from config import SECRET_KEY

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)