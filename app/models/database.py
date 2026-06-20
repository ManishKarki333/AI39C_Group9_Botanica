import pymysql
from pymysql.constants import CLIENT 
from werkzeug.security import generate_password_hash  
import config                                         


class Database:
    def __init__(self):
        """Open a database connection when object is created."""
        try:
            host = config.MYSQL_HOST
            user = config.MYSQL_USER
            password = config.MYSQL_PASSWORD
            database = config.MYSQL_DATABASE

            if host is None or user is None or password is None or database is None:
                raise ValueError("Database configuration values must be set")

            self.__connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                cursorclass=pymysql.cursors.DictCursor,
                charset="utf8mb4",
                use_unicode=True,
                autocommit=False,
                client_flag=CLIENT.FOUND_ROWS 
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
        """Run a data-modifying query. Returns lastrowid for INSERTs, or rowcount for updates/deletes."""
        cursor = self.__connection.cursor()
        try:
            cursor.execute(query, params)
            self.__connection.commit()
            
            # FIX: Force connection synchronization to clear transaction snapshot caching.
            # This ensures that when the page redirects to the dashboard, the SELECT queries
            # read the fresh updates immediately from the disk.
            self.__connection.commit()
            
            clean_query = query.strip().upper()
            
            if clean_query.startswith("INSERT"):
                return cursor.lastrowid
            else:
                # With CLIENT.FOUND_ROWS active, this safely returns 1 if row matches WHERE criteria
                return cursor.rowcount
                
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
                scientific_name VARCHAR(100) NOT NULL,
                description TEXT,
                benefit_category VARCHAR(50) NOT NULL,
                price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
                stock_quantity INT NOT NULL DEFAULT 0,
                image_url VARCHAR(255) DEFAULT 'default_herb.png',
                merchant_id INT DEFAULT NULL,
                whatsapp_number VARCHAR(20) DEFAULT NULL,
                reference_url VARCHAR(255) DEFAULT NULL,
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
                order_status ENUM('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Pending',
                payment_status ENUM('Pending', 'Paid', 'Failed') DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

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

        db.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                herb_id INT NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (herb_id) REFERENCES herbs(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                target_type ENUM('product', 'merchant') NOT NULL,
                target_id INT NOT NULL,
                reason VARCHAR(255) NOT NULL,
                description TEXT,
                status ENUM('pending', 'resolved') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        try:
            cats = db.fetch_all("SELECT * FROM categories")
            if not cats:
                for cat_name in ["Sleep", "Digestion", "Energy", "Immunity"]:
                    db.execute("INSERT INTO categories (name) VALUES (%s)", (cat_name,))
        except Exception as e:
            print("Failed to seed categories:", e)

        # Structural sanity checks for secondary columns
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
        try:
            db.execute("ALTER TABLE herbs ADD COLUMN reference_url VARCHAR(255) DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE herbs DROP INDEX scientific_name")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE herbs ADD COLUMN qr_payment_type VARCHAR(50) DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE herbs ADD COLUMN qr_code_url VARCHAR(255) DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE orders ADD COLUMN merchant_id INT DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE orders ADD COLUMN shipping_address TEXT DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(50) NOT NULL DEFAULT 'Unpaid'")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE orders ADD CONSTRAINT fk_orders_merchant FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE CASCADE")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE order_items ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE orders MODIFY COLUMN order_status ENUM('Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Pending'")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE orders MODIFY COLUMN payment_status VARCHAR(50) NOT NULL DEFAULT 'Unpaid'")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE orders ADD COLUMN payment_method VARCHAR(50) DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE orders ADD COLUMN transaction_screenshot VARCHAR(255) DEFAULT NULL")
        except Exception:
            pass
        try:
            db.execute("ALTER TABLE orders ADD COLUMN cancellation_reason TEXT DEFAULT NULL")
        except Exception:
            pass

        admin = db.fetch_one(
            "SELECT * FROM users WHERE email = %s",
            ("admin@admin.com",)
        )

        if not admin:
            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ("Admin", "admin@admin.com",
                 generate_password_hash("admin123"), "admin"),
            )
            print("Default admin account created!")

        db.close()