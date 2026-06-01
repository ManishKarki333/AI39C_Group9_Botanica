import pymysql
import config


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
            )

            print("Database connected successfully!")

        except pymysql.MySQLError as e:
            print("Database connection failed!")
            print("Error:", e)

    # ── Fetch One Record ─────────────────────────────────────
    def fetch_one(self, query, params=None):
        """Run a query and return ONE result (or None)."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        cursor.close()
        return result

    # ── Fetch All Records ────────────────────────────────────
    def fetch_all(self, query, params=None):
        """Run a query and return ALL results as a list."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results

    # ── Execute (INSERT / UPDATE / DELETE) ───────────────────
    def execute(self, query, params=None):
        """Run a query that changes data (INSERT, UPDATE, DELETE)."""
        cursor = self.__connection.cursor()
        cursor.execute(query, params)
        self.__connection.commit()
        cursor.close()

    # ── Close Connection ─────────────────────────────────────
    def close(self):
        """Close the database connection."""
        self.__connection.close()

    # ── Static Method: Create ALL tables on app startup ──────
    @staticmethod
    def create_tables():
        """
        Create ALL database tables if they don't already exist.

        @staticmethod: belongs to the class but doesn't need
        'self' — it doesn't use any instance data.
        You call it as: Database.create_tables()
        """
        db = Database()

        # ── Table 1: Users ───────────────────────────────────
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                name       VARCHAR(100) NOT NULL,
                email      VARCHAR(100) NOT NULL UNIQUE,
                password   VARCHAR(255) NOT NULL,
                role       VARCHAR(20)  NOT NULL DEFAULT 'user',
                created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Table 2: Contact Messages ────────────────────────
        db.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name  VARCHAR(100) NOT NULL,
                email      VARCHAR(255) NOT NULL,
                inquiry    VARCHAR(100),
                subject    VARCHAR(255) NOT NULL,
                message    TEXT         NOT NULL,
                created_at DATETIME     DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ── Seed: Default Admin Account ──────────────────────
        # Create a default admin user if one doesn't exist yet
        admin = db.fetch_one(
            "SELECT * FROM users WHERE email = %s", ("admin@admin.com",)
        )
        if not admin:
            from werkzeug.security import generate_password_hash
            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ("Admin", "admin@admin.com", generate_password_hash("admin123"), "admin"),
            )
            print("Default admin account created!")

        db.close()
