import pymysql
import config


class Database:

    def __init__(self):
        """Open a database connection when object is created."""
        try:
            self.__connection = pymysql.connect(
                host=config.MYSQL_HOST,
                user=config.MYSQL_USER,
                password=config.MYSQL_PASSWORD,
                database=config.MYSQL_DATABASE,
                cursorclass=pymysql.cursors.DictCursor,
                charset="utf8mb4",  # Fix: Ensures special botanical symbols display safely
                use_unicode=True,
            )
            print("Database connected successfully!")

        except pymysql.MySQLError as e:
            print("Database connection failed!")
            print("Error:", e)

    def fetch_one(self, query, params=None):
        """Run a query and return ONE result (or None)."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result

    def fetch_all(self, query, params=None):
        """Run a query and return ALL results as a list."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results

    def execute(self, query, params=None):
        """Run a query that changes data (INSERT, UPDATE, DELETE)."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        self.__connection.commit()
        cursor.close()

    def close(self):
        """Close the database connection."""
        self.__connection.close()

    # ── Static Method: Create tables on app startup ─────────

    @staticmethod
    def create_tables():
        """Create database tables updated for Search, Filtering, and Merchant features."""
        db = Database()

        # 1. Users Table (Maintains roles for Customers, Merchants, and Admins)
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 2. Herbs Table (Updated with Image, Stock, Price, and Benefit filtering fields)
        db.execute("""
            CREATE TABLE IF NOT EXISTS herbs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                common_name VARCHAR(100) NOT NULL,
                scientific_name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                benefit_category VARCHAR(50) NOT NULL, -- Fix: Maps to US 3 (Sleep, Digestion, etc.)
                price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                stock_quantity INT NOT NULL DEFAULT 0,
                image_url VARCHAR(255) DEFAULT 'default_herb.png', -- Fix: Keeps UI card grading-ready
                merchant_id INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Create default admin if not exists
        admin = db.fetch_one(
            "SELECT * FROM users WHERE email = %s", ("admin@admin.com",)
        )
        if not admin:
            from werkzeug.security import generate_password_hash

            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (
                    "Admin",
                    "admin@admin.com",
                    generate_password_hash("admin123"),
                    "admin",
                ),
            )

        db.close()