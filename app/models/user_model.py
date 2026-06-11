"""
=============================================================
  OOP Concept: INHERITANCE, ENCAPSULATION & POLYMORPHISM
=============================================================
  - Inheritance: User inherits from BaseModel, so it gets
    find_by_id(), find_all(), delete_by_id() for FREE.
  - Encapsulation: Password is kept private (__password).
    Outside code cannot access user.__password directly.
    We use a setter method to control how it's changed.
  - Polymorphism: User defines its own 'table' property,
    which overrides the abstract one from BaseModel.
    Same interface, different behavior = polymorphism.
=============================================================
"""

from werkzeug.security import generate_password_hash, check_password_hash
from .base_model import BaseModel
from .database import Database


class User(BaseModel):
    """
    User Model — represents a single user in our app.

    Inherits from BaseModel:
      - find_by_id(id)
      - find_by(column, value)
      - find_all()
      - count_all()
      - delete_by_id(id)
    """

    @property
    def table(self):
        """Tell BaseModel which database table to use."""
        return "users"

    def __init__(self, name=None, email=None, password=None, role="user"):
        """
        Create a User object.

        Encapsulation:
          - __password is PRIVATE (double underscore).
          - It can only be set through set_password().
          - This protects the password from accidental access.
        """
        self.name = name
        self.email = email
        self.__password: str | None = None   # ✅ declared with type hint
        self.role = role

        if password:
            self.set_password(password)

    def set_password(self, plain_password: str) -> None:
        """Hash and store the password securely."""
        self.__password = generate_password_hash(plain_password)

    def get_hashed_password(self) -> str | None:
        """
        NEW: Safe internal getter for the hashed password.
        Used by from_db() to assign the password cleanly
        without triggering Pylance name-mangling warnings.
        """
        return self.__password

    def set_hashed_password(self, hashed: str) -> None:
        """
        NEW: Directly assign an already-hashed password.
        Used by from_db() to restore a User from the database
        without re-hashing the already hashed value.
        """
        self.__password = hashed

    def check_password(self, plain_password: str) -> bool:
        """Check if the given password matches the stored hash."""
        if self.__password is None:
            return False
        return check_password_hash(self.__password, plain_password)

    def save(self) -> None:
        """Insert this user into the database."""
        db = Database()
        db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (self.name, self.email, self.__password, self.role),
        )
        db.close()

    def update(self, user_id: int, update_password: bool = False) -> None:
        """
        Update user in database.
        If update_password=True, the password is also updated.
        """
        db = Database()
        if update_password:
            db.execute(
                "UPDATE users SET name=%s, email=%s, password=%s, role=%s WHERE id=%s",
                (self.name, self.email, self.__password, self.role, user_id),
            )
        else:
            db.execute(
                "UPDATE users SET name=%s, email=%s, role=%s WHERE id=%s",
                (self.name, self.email, self.role, user_id),
            )
        db.close()

    def update_profile(self, user_id: int, update_password: bool = False) -> None:
        """
        Update profile (name, email, and optionally password).
        Used when a user edits their own profile (no role change).
        """
        db = Database()
        if update_password:
            db.execute(
                "UPDATE users SET name=%s, email=%s, password=%s WHERE id=%s",
                (self.name, self.email, self.__password, user_id),
            )
        else:
            db.execute(
                "UPDATE users SET name=%s, email=%s WHERE id=%s",
                (self.name, self.email, user_id),
            )
        db.close()

    def email_exists(self, exclude_id: int | None = None) -> bool:
        """
        Check if this user's email is already in the database.
        exclude_id: ignore this user ID when updating.
        """
        db = Database()
        if exclude_id is not None:
            result = db.fetch_one(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                (self.email, exclude_id),
            )
        else:
            result = db.fetch_one(
                "SELECT id FROM users WHERE email = %s",
                (self.email,),
            )
        db.close()
        return result is not None

    @classmethod
    def from_db(cls, data: dict | None) -> "User | None":
        """
        Create a User object from a database dictionary.
        FIX: Uses set_hashed_password() instead of name-mangling
        to avoid Pylance private attribute warnings.
        """
        if data is None:
            return None

        user = cls()
        user.name = data["name"]
        user.email = data["email"]
        user.role = data["role"]

        # FIX: clean setter instead of _User__password = ...
        user.set_hashed_password(data["password"])
        return user

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"User(name={self.name}, email={self.email}, role={self.role})"

    def __repr__(self) -> str:
        """Developer-friendly representation for debugging."""
        return f"<User email={self.email}>"
