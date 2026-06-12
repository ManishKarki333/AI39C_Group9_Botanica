"""
=============================================================
  OOP Concept: ABSTRACTION & INHERITANCE (Base Model)
=============================================================
  - Abstraction: We define WHAT every model should do
    (find, create, update, delete) without saying HOW.
  - Inheritance: Child classes (like User, ContactMessage)
    will inherit these methods and reuse them automatically.
  - Encapsulation: The database connection details are
    hidden inside this class — outside code never sees them.
=============================================================
"""

from abc import ABC, abstractmethod
from typing import Any
from .database import Database


class BaseModel(ABC):
    """
    Abstract Base Class for all models.

    ABC = Abstract Base Class
    - You CANNOT create an object of BaseModel directly.
    - Child classes MUST define the 'table' property.
    - Child classes INHERIT all the helper methods below.
    """

    @property
    @abstractmethod
    def table(self) -> str:
        """Each child model must specify its database table name."""
        pass

    def _validate_identifier(self, identifier: str) -> str:
        """
        Allow only simple SQL identifiers like column/table names.
        Prevents SQL injection in dynamic column/order usage.
        """
        if not isinstance(identifier, str) or not identifier.replace("_", "").isalnum():
            raise ValueError(f"Invalid SQL identifier: {identifier}")
        return identifier

    def find_by_id(self, record_id: int) -> dict[str, Any] | None:
        """Find a single record by its ID."""
        db = Database()
        result = db.fetch_one(
            f"SELECT * FROM {self.table} WHERE id = %s",
            (record_id,)
        )
        db.close()
        return result

    def find_by(self, column: str, value: Any) -> dict[str, Any] | None:
        """Find a single record by any allowed column."""
        column = self._validate_identifier(column)
        db = Database()
        result = db.fetch_one(
            f"SELECT * FROM {self.table} WHERE {column} = %s",
            (value,)
        )
        db.close()
        return result

    def find_all(self, order_by: str = "id") -> list[dict[str, Any]]:
        """Get all records from the table, ordered by a valid column."""
        order_by = self._validate_identifier(order_by)
        db = Database()
        raw = db.fetch_all(
            f"SELECT * FROM {self.table} ORDER BY {order_by}"
        )
        db.close()

        # ✅ FIX: explicitly convert to list — db.fetch_all()
        # may return a tuple, None, or list depending on the
        # database driver. We always guarantee a list[dict] here.
        if raw is None:
            return []
        return list(raw)

    def count_all(self) -> int:
        """Count total records in the table."""
        db = Database()
        result = db.fetch_one(
            f"SELECT COUNT(*) AS total FROM {self.table}"
        )
        db.close()

        # ✅ FIX: guard against None before subscripting
        if result is None:
            return 0
        return int(result["total"])

    def delete_by_id(self, record_id: int) -> None:
        """Delete a record by its ID."""
        db = Database()
        db.execute(
            f"DELETE FROM {self.table} WHERE id = %s",
            (record_id,)
        )
        db.close()
