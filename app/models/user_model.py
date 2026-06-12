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

from __future__ import annotations
from typing import Any
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.base_model import BaseModel     # ✅ FIX: absolute import
from app.models.database import Database        # ✅ FIX: absolute import


class User(BaseModel):
    """
    User Model - represents a single user in our app.

    Inherits from BaseModel:
      - find_by_id(id)
      - find_by(column, value)
      - find_all()
      - count_all()
      - delete_by_id(id)
    """

    @property
    def table(self) -> str:
        """Tell BaseModel which database table to use."""
        return "users"

    def __init__(
        self,
        name: str | None = None,
        email: str | None = None,
        password: str | None = None,
        role: str = "user",
        profile_pic: str | None = None,
        certification_badge: str | None = None,
        is_active: int = 1,
    ) -> None:
        self.name = name
        self.email = email
        self.__password: str | None = None
        self.role = role
        self.profile_pic = profile_pic
        self.certification_badge = certification_badge
        self.is_active = is_active

        if password:
            self.set_password(password)

    def set_password(self, plain_password: str) -> None:
        """Hash and store the password securely."""
        self.__password = generate_password_hash(plain_password)

    def set_hashed_password(self, hashed: str) -> None:
        """
        Directly assign an already-hashed password.
        Used by from_db() to avoid Pylance name-mangling warnings.
        """
        self.__password = hashed

    def get_hashed_password(self) -> str | None:
        """Return the hashed password (for internal use only)."""
        return self.__password

    def check_password(self, plain_password: str) -> bool:
        """Check if the given password matches the stored hash."""
        if self.__password is None:
            return False
        return check_password_hash(self.__password, plain_password)

    def save(self) -> None:
        """Insert this user into the database."""
        db = Database()
        db.execute(
            "INSERT INTO users (name, email, password, role, profile_pic, certification_badge, is_active) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (self.name, self.email, self.__password, self.role, self.profile_pic, self.certification_badge, self.is_active),
        )
        db.close()

    def update(self, user_id: int, update_password: bool = False) -> None:
        """Update user in the database."""
        db = Database()
        if update_password:
            db.execute(
                "UPDATE users SET name=%s, email=%s, password=%s, role=%s, profile_pic=%s, certification_badge=%s, is_active=%s WHERE id=%s",
                (self.name, self.email, self.__password, self.role, self.profile_pic, self.certification_badge, self.is_active, user_id),
            )
        else:
            db.execute(
                "UPDATE users SET name=%s, email=%s, role=%s, profile_pic=%s, certification_badge=%s, is_active=%s WHERE id=%s",
                (self.name, self.email, self.role, self.profile_pic, self.certification_badge, self.is_active, user_id),
            )
        db.close()

    def update_profile(self, user_id: int, update_password: bool = False) -> None:
        db = Database()
        if update_password:
            db.execute(
                "UPDATE users SET name=%s, email=%s, password=%s, profile_pic=%s, certification_badge=%s WHERE id=%s",
                (self.name, self.email, self.__password, self.profile_pic, self.certification_badge, user_id),
            )
        else:
            db.execute(
                "UPDATE users SET name=%s, email=%s, profile_pic=%s, certification_badge=%s WHERE id=%s",
                (self.name, self.email, self.profile_pic, self.certification_badge, user_id),
            )
        db.close()

    def email_exists(self, exclude_id: int | None = None) -> bool:
        """Check if this user's email is already in the database."""
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
    def from_db(cls, data: dict[str, Any] | None) -> User | None:
        """
        Create a User object from a database row dictionary.
        Uses set_hashed_password() to avoid name-mangling issues.
        """
        if data is None:
            return None

        user = cls()
        user.name  = data["name"]
        user.email = data["email"]
        user.role  = data["role"]
        user.profile_pic = data.get("profile_pic")
        user.certification_badge = data.get("certification_badge")
        user.is_active = data.get("is_active", 1)
        user.set_hashed_password(data["password"])  # ✅ clean, no mangling
        return user

    def __str__(self) -> str:
        return f"User(name={self.name}, email={self.email}, role={self.role})"

    def __repr__(self) -> str:
        return f"<User email={self.email}>"
