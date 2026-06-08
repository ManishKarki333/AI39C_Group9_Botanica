import pymysql
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
                db=database,
                cursorclass=pymysql.cursors.DictCursor,
                charset="utf8mb4",
                use_unicode=True,
            )
            print("Database connected successfully!")

        except pymysql.MySQLError as e:
            print("Database connection failed!")
            print("Error:", e)
            raise

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
        """Run a data-modifying query. Returns the last row ID if an INSERT occurs."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        self.__connection.commit()
        last_id = cursor.lastrowid  # Crucial for matching order_items to order headers!
        cursor.close()
        return last_id

    def close(self):
        """Close the database connection."""
        self.__connection.close()

    @staticmethod
    def create_tables():
        """Create database tables updated for Search, Filtering, Merchant, and Transactional Loops."""
        db = Database()

        # Users table
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

        # Contact messages table
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

        # Herbs table
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # 3. Orders Table (NEW - Tracks core transactions and logistics metrics)
        db.execute("""
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
                herb_id INT NOT NULL,
                merchant_id INT NOT NULL, -- Identifies which supplier handles fulfillment tracking
                quantity INT NOT NULL DEFAULT 1,
                price_at_purchase DECIMAL(10, 2) NOT NULL, -- Safeguards historical financials if cost updates later
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (herb_id) REFERENCES herbs(id) ON DELETE RESTRICT,
                FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # 5. Merchant Certificates Table (NEW - Backs the validation badges for vendor trust metrics)
        db.execute("""
            CREATE TABLE IF NOT EXISTS merchant_certificates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                merchant_id INT NOT NULL,
                certificate_name VARCHAR(150) NOT NULL, -- (e.g., "Certified Organic Wildcrafter")
                file_path VARCHAR(255) NOT NULL, -- Location where secure document file remains on the server
                is_verified BOOLEAN NOT NULL DEFAULT FALSE, -- Allows admin toggle approval controls
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (merchant_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Create default admin if not exists
        admin = db.fetch_one(
            "SELECT * FROM users WHERE email = %s",
            ("admin@admin.com",)
        )

        if not admin:
            from werkzeug.security import generate_password_hash

            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ("Admin", "admin@admin.com", generate_password_hash("admin123"), "admin"),
            )
            print("Default admin account created!")

        db.close()