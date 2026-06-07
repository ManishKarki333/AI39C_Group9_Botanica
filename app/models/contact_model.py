"""
=============================================================
  OOP Concept: INHERITANCE & POLYMORPHISM (Contact Model)
=============================================================
  - Inheritance: ContactMessage inherits all shared DB
    methods from BaseModel (find_by_id, find_all, etc.)
  - Polymorphism: Defines its own 'table' property and
    its own save() method for contact form submissions.
  - Encapsulation: All DB logic is hidden inside this
    class — the controller just calls .save().
=============================================================
"""

from app.models.base_model import BaseModel
from app.models.database import Database
from datetime import datetime


class ContactMessage(BaseModel):
    """
    ContactMessage Model — stores every contact form submission.

    Inherits from BaseModel:
      - find_by_id(id)
      - find_by(column, value)
      - find_all()
      - count_all()
      - delete_by_id(id)
    """

    # ── Polymorphism: Override the abstract 'table' property ──
    @property
    def table(self):
        """Tell BaseModel which database table to use."""
        return "contact_messages"

    # ── Constructor ─────────────────────────────────────────
    def __init__(
        self,
        first_name=None,
        last_name=None,
        email=None,
        inquiry=None,
        subject=None,
        message=None,
    ):
        """
        Create a ContactMessage object with all form fields.
        created_at is automatically set to the current time.
        """
        self.first_name = first_name
        self.last_name  = last_name
        self.email      = email
        self.inquiry    = inquiry
        self.subject    = subject
        self.message    = message
        self.created_at = datetime.now()

    # ── Create: Save contact message to the database ─────────
    def save(self):
        """Insert this contact message into the database."""
        db = Database()
        db.execute(
            """
            INSERT INTO contact_messages
                (first_name, last_name, email, inquiry, subject, message, created_at)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                self.first_name,
                self.last_name,
                self.email,
                self.inquiry,
                self.subject,
                self.message,
                self.created_at,
            ),
        )
        db.close()

    # ── Helper: Full name convenience property ───────────────
    @property
    def full_name(self):
        """Returns the full name of the sender."""
        return f"{self.first_name} {self.last_name}"

    # ── Magic Methods ─────────────────────────────────────────
    def __str__(self):
        return f"ContactMessage(from={self.full_name}, subject={self.subject})"

    def __repr__(self):
        return f"<ContactMessage email={self.email}>"
