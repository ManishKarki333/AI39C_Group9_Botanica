import pymysql
from werkzeug.security import generate_password_hash  # ✅ moved to top
import config                                          # ✅ root-level config


class Database:
    def __init__(self):
        """Open a database connection when object is created."""
        try:
            host     = config.MYSQL_HOST
            user     = config.MYSQL_USER
            password = config.MYSQL_PASSWORD
            database = config.MYSQL_DATABASE

            if host is None or user is None or password is None or database is None:
                raise ValueError("Database configuration values must be set")

            self.__connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                db=database,
                cursorclass=pymysql.cursors.DictCursor,
                charset="utf8mb4",
                use_unicode=True,
                autocommit=False,
            )
            print("Database connected successfully!")

        except pymysql.MySQLError as e:
            print("Database connection failed!")
            print("Error:", e)
            raise

    def fetch_one(self, query, params=None):
        """Run a query and return one result or None."""
        cursor = self.__connection.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        """Run a query and return all results as a list."""
        cursor = self.__connection.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()

    def execute(self, query, params=None):
<<<<<<< HEAD
        """Run a query that changes data."""
=======
        """Run a data-modifying query. Returns the last row ID if an INSERT occurs."""
>>>>>>> ffbbe146b7b51e9e67d18c219562ea8c3f8932ae
        cursor = self.__connection.cursor()
        try:
            cursor.execute(query, params)
            self.__connection.commit()
        except Exception:
            self.__connection.rollback()
            raise
        finally:
            cursor.close()

    def close(self):
        """Close the database connection."""
        if self.__connection:
            self.__connection.close()

    @staticmethod
    def create_tables():
<<<<<<< HEAD
        """Create all required database tables on app startup."""
=======
        """Create database tables updated for Search, Filtering, Merchant, and Transactional Loops."""
>>>>>>> ffbbe146b7b51e9e67d18c219562ea8c3f8932ae
        db = Database()

        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                inquiry VARCHAR(100),
                subject VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS herbs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                common_name VARCHAR(100) NOT NULL,
                scientific_name VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
<<<<<<< HEAD
                benefit_category VARCHAR(50) NOT NULL,
                price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                stock_quantity INT NOT NULL DEFAULT 0,
                image_url VARCHAR(255) DEFAULT 'default_herb.png',
=======
                benefit_category VARCHAR(50) NOT NULL, -- Maps to US 3 (Sleep, Digestion, etc.)
                price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                stock_quantity INT NOT NULL DEFAULT 0,
                image_url VARCHAR(255) DEFAULT 'default_herb.png', -- Keeps UI card grading-ready
>>>>>>> ffbbe146b7b51e9e67d18c219562ea8c3f8932ae
                merchant_id INT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        db.execute("""
<<<<<<< HEAD
            CREATE TABLE IF NOT EXISTS cart_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
=======
            CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            merchant_id INT NOT NULL, -- Added to enable Merchant Dashboard filtering
            total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
            shipping_address TEXT NOT NULL, -- Added for order fulfillment
            delivery_date DATE NOT NULL,
            delivery_window VARCHAR(100) NOT NULL,
            order_status ENUM('Pending', 'Shipped', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Pending',
            payment_status ENUM('Pending', 'Paid', 'Failed') DEFAULT 'Pending', -- Added for transactional integrity
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 4. Order Items Table (NEW - Breakdown for shopping carts supporting multi-vendor line items)
        db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
>>>>>>> ffbbe146b7b51e9e67d18c219562ea8c3f8932ae
                herb_id INT NOT NULL,
                quantity INT NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_herb (user_id, herb_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (herb_id) REFERENCES herbs(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)


        admin = db.fetch_one(
            "SELECT * FROM users WHERE email = %s",
            ("admin@admin.com",)
        )

        if not admin:
            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ("Admin", "admin@admin.com", generate_password_hash("admin123"), "admin"),
            )
            print("Default admin account created!")

<<<<<<< HEAD
        db.close()

=======
        db.close()
>>>>>>> ffbbe146b7b51e9e67d18c219562ea8c3f8932ae
