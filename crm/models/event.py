import datetime

from sqlalchemy import (
    Integer,
    String,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import (
    relationship,
    validates,
    Mapped,
    mapped_column,
    aliased,
    validates,
)
from sqlalchemy import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import select
from sqlalchemy import CheckConstraint, case
from ..models.user import User
from ..utils.validations import Validations

from .base import AbstractBase


class Event(AbstractBase):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("date_end > date_start", name="check_event_dates"),
    )

    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    support_contact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    date_start: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    date_end: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str] = mapped_column(String(300))
    attendees: Mapped[int] = mapped_column(Integer)

    notes = relationship(
        "EventNote", back_populates="event", cascade="all, delete-orphan"
    )
    contract = relationship("Contract", back_populates="event")
    support_contact = relationship("User", back_populates="events")

    # Type ignore car l'IDE ne comprend pas qu'ils doivent avoir le même nom
    @hybrid_property
    def support_contact_name(self):  # type: ignore
        return (
            self.support_contact.username if self.support_contact else "Aucun contact"
        )

    @support_contact_name.expression
    def support_contact_name(cls):
        UserAlias = aliased(User)
        return (
            select(User.username)
            .join(UserAlias, UserAlias.id == User.id)
            .where(UserAlias.id == cls.support_contact_id)
            .scalar_subquery()
        )

    @hybrid_property
    def is_assigned(self):  # type: ignore
        return self.support_contact is not None

    @is_assigned.expression
    def is_assigned(cls):
        return case({cls.support_contact_id != None: True}, else_=False).label(
            "is_assigned"
        )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, location='{self.location}', attendees={self.attendees})>"

    @validates("date_start", "date_end")
    def validate_dates(self, key, value):
        if not isinstance(value, datetime.datetime):
            raise ValueError(f"{key} must be a datetime object")

        # Validation de la cohérence des dates
        if key == "date_end":
            current_start = getattr(self, "date_start", None)
            if current_start is not None and value <= current_start:
                raise ValueError("date_end must be after date_start")

        elif key == "date_start":
            current_end = getattr(self, "date_end", None)
            if current_end is not None and value >= current_end:
                raise ValueError("date_start must be before date_end")

        return value

    @validates("attendees")
    def validate_attendees(self, key, value):
        if not isinstance(value, int):
            raise ValueError(f"{key} must be an integer")

        Validations.validate_positive_integer(value)

        if value <= 0:
            raise ValueError(f"{key} cannot be negative or zero")

        return value

    try:
        from ..tests.conftest import TestingBase as BaseForTests
    except ImportError:
        from .base import AbstractBase as BaseForTests


class EventNote(AbstractBase):
    __tablename__ = "event_notes"

    event_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    note: Mapped[str] = mapped_column(String(2048), nullable=False)

    event = relationship("Event", back_populates="notes")

    def __repr__(self) -> str:
        return f"<EventNote(id={self.id}, event_id={self.event_id})>"

    try:
        from ..tests.conftest import TestingBase as BaseForTests
    except ImportError:
        from .base import AbstractBase as BaseForTests
