import re
import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    func,
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy import Enum as PgEnum
from sqlalchemy import CheckConstraint
from .database import Base
from decimal import Decimal
from functools import partial

utcnow = partial(datetime.datetime.now, datetime.timezone.utc)


class AbstractBase(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class Contract(AbstractBase):
    __tablename__ = "contracts"
    __table_args__ = (
        CheckConstraint("amount_due <= amount_total", name="check_amount_due"),
    )

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    sales_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount_total = Column(Numeric(10, 2), nullable=False)
    amount_due = Column(Numeric(10, 2), nullable=False)
    is_signed = Column(Boolean, default=False, nullable=False)

    client = relationship("Client", back_populates="contracts")
    sales_contact = relationship("User", back_populates="contracts")
    event = relationship("Event", back_populates="contract", uselist=False)

    def __repr__(self) -> str:
        return f"<Contract(id={self.id}, total={self.amount_total}, signed={self.is_signed})>"

    @validates("amount_due", "amount_total")
    def validate_amounts(self, key, value):
        total = self.get("amount_total")
        due = self.get("amount_due")

        if not isinstance(value, (Decimal, int, float)):
            raise ValueError(f"{key} must be a numeric type (Decimal, int, float)")

        if isinstance(value, Decimal) and value < 0:
            raise ValueError(f"{key} cannot be negative")

        if isinstance(total, Decimal) and total <= 0:
            raise ValueError("amount_total cannot be negative or zero")

        if isinstance(total, Decimal) and isinstance(due, Decimal):
            if due > total:
                raise ValueError("amount_due cannot exceed amount_total")

        return value


class Event(AbstractBase):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("date_end > date_start", name="check_event_dates"),
    )

    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    support_contact_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    date_start = Column(DateTime, nullable=False)
    date_end = Column(DateTime, nullable=False)
    location = Column(String(255))
    attendees = Column(Integer)
    notes = Column(String(1024))

    contract = relationship("Contract", back_populates="event")
    support_contact = relationship("User", back_populates="events")

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, location='{self.location}', attendees={self.attendees})>"

    @validates("date_start", "date_end")
    def validate_dates(self, key, value):

        if not isinstance(value, datetime):
            raise ValueError(f"{key} must be a datetime object")

        if key == "date_end" and value < self.date_start:
            raise ValueError("date_end must be after date_start")
        return value

    @validates("attendees")
    def validate_attendees(self, key, value):
        if not isinstance(value, int):
            raise ValueError(f"{key} must be an integer")

        if value < 0:
            raise ValueError(f"{key} cannot be negative or zero")

        return value


class User(AbstractBase):
    __tablename__ = "users"

    username = Column(String, nullable=False, unique=True)
    # La logique de hash est à implémenter plus tard
    password_hash = Column(String(255), nullable=False)
    # Enum pour les rôles (sales, support, management)
    role = Column(
        PgEnum("sales", "support", "management", name="user_roles"), nullable=False
    )

    clients = relationship("Client", back_populates="sales_contact")
    contracts = relationship("Contract", back_populates="sales_contact")
    events = relationship("Event", back_populates="support_contact")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Client(AbstractBase):
    __tablename__ = "clients"
    __table_args__ = (CheckConstraint("email != ''", name="check_client_email"),)

    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String)
    company_name = Column(String)

    # Many Client to One User
    sales_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    sales_contact = relationship("User", back_populates="clients")
    contracts = relationship("Contract", back_populates="client")

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.full_name}')>"

    @validates("email")
    def validate_email(self, key, value):
        email_regex = r"^\S+@\S+\.\S+$"

        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")

        if not re.match(email_regex, value):
            raise ValueError(f"{key} must be a valid email address")

        return value

    @validates("phone")
    def validate_phone(self, key, value):
        phone_regex = r"^\\+?[1-9][0-9]{7,14}$"

        if value and not re.match(phone_regex, value):
            raise ValueError(f"{key} must be a valid phone number")

        return value
