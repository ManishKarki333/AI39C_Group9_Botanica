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
        """Run a data-modifying query. Returns the last row ID if an INSERT occurs."""
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
        """Create database tables updated for Search, Filtering, Merchant, and Transactional Loops."""
        db = Database()

        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                profile_pic VARCHAR(255) DEFAULT NULL,
                certification_badge VARCHAR(255) DEFAULT NULL,
                is_active TINYINT DEFAULT 1,
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
                benefit_category VARCHAR(50) NOT NULL, -- Maps to US 3 (Sleep, Digestion, etc.)
                price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                stock_quantity INT NOT NULL DEFAULT 0,
                image_url VARCHAR(255) DEFAULT 'default_herb.png', -- Keeps UI card grading-ready
                merchant_id INT DEFAULT NULL,
                whatsapp_number VARCHAR(20) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                herb_id INT NOT NULL,
                quantity INT NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_user_herb (user_id, herb_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (herb_id) REFERENCES herbs(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                merchant_id INT NOT NULL,
                total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                shipping_address TEXT NOT NULL,
                delivery_date DATE NOT NULL,
                delivery_window VARCHAR(100) NOT NULL,
                order_status ENUM('Pending', 'Shipped', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Pending',
                payment_status ENUM('Pending', 'Paid', 'Failed') DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 4. Order Items Table (Breakdown for multi-vendor line items)
        db.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                herb_id INT NOT NULL,
                quantity INT NOT NULL DEFAULT 1,
                price_at_purchase DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (herb_id) REFERENCES herbs(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 5. Reviews Table
        db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INT AUTO_INCREMENT PRIMARY KEY,
                herb_id INT NOT NULL,
                user_id INT NOT NULL,
                rating INT NOT NULL,
                comment TEXT NOT NULL,
                image_url VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (herb_id) REFERENCES herbs(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 6. Price History Table
        db.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                herb_id INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (herb_id) REFERENCES herbs(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Add OTP columns to users if they do not exist
        try:
            db.execute("ALTER TABLE users ADD COLUMN otp_code VARCHAR(6) DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE users ADD COLUMN otp_expiry DATETIME DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE users ADD COLUMN profile_pic VARCHAR(255) DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE users ADD COLUMN certification_badge VARCHAR(255) DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE users ADD COLUMN is_active TINYINT DEFAULT 1")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE herbs ADD COLUMN whatsapp_number VARCHAR(20) DEFAULT NULL")
        except Exception:
            pass

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

        db.close()
