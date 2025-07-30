import re
import datetime

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

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
from sqlalchemy import CheckConstraint
from .database import Base
from decimal import Decimal
from functools import partial

utcnow = partial(datetime.datetime.now, datetime.timezone.utc)

ph = PasswordHasher(
    time_cost=3,  # nombre d'itérations
    memory_cost=65536,  # mémoire utilisée en KB (64MB ici)
    parallelism=4,  # threads
)


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
        # Validation du type
        if not isinstance(value, (Decimal, int, float)):
            raise ValueError(f"{key} must be a numeric type (Decimal, int, float)")

        # Convertir en Decimal pour la précision
        if isinstance(value, (int, float)):
            value = Decimal(str(value))

        # Validation de base : pas de valeurs négatives
        if value < 0:
            raise ValueError(f"{key} cannot be negative")

        # Validation spécifique pour amount_total
        if key == "amount_total":
            if value <= 0:
                raise ValueError("amount_total must be greater than zero")

            # Vérifier la cohérence avec amount_due existant
            current_due = getattr(self, "amount_due", None)
            if (
                current_due is not None
                and isinstance(current_due, Decimal)
                and current_due > value
            ):
                raise ValueError("amount_due cannot exceed amount_total")

        # Validation spécifique pour amount_due
        elif key == "amount_due":
            current_total = getattr(self, "amount_total", None)
            if (
                current_total is not None
                and isinstance(current_total, Decimal)
                and value > current_total
            ):
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

        if value <= 0:
            raise ValueError(f"{key} cannot be negative or zero")

        return value


class User(AbstractBase):
    __tablename__ = "users"

    employee_number = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)

    # Relation many-tomany via la table d'association user_roles
    user_roles = relationship("UserRole", back_populates="user")

    clients = relationship("Client", back_populates="sales_contact")
    contracts = relationship("Contract", back_populates="sales_contact")
    events = relationship("Event", back_populates="support_contact")

    @property
    def roles(self):
        return [user_role.role for user_role in self.user_roles]

    def set_password(self, raw_password: str):
        self.password_hash = ph.hash(raw_password)

    def verify_password(self, raw_password: str) -> bool:
        try:
            # Comme password_hash est typé comme String, on s'assure qu'il est traité comme tel
            hash_value = (
                str(self.password_hash) if self.password_hash is not None else ""
            )
            return ph.verify(hash_value, raw_password)
        except VerifyMismatchError:
            return False

    def __repr__(self) -> str:
        role_names = ", ".join([role.name for role in self.roles])
        return (
            f"<User(id={self.id}, username='{self.username}', "
            f"employee_number={self.employee_number}, roles=[{role_names}])>"
        )


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

        if value is None:
            raise ValueError("Email cannot be None")

        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")

        if not re.match(email_regex, value):
            raise ValueError(f"{key} must be a valid email address")

        return value

    @validates("phone")
    def validate_phone(self, key, value):
        phone_regex = r"^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$"

        if value and not re.match(phone_regex, value):
            raise ValueError(f"{key} must be a valid phone number")

        return value


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)

    user_roles = relationship("UserRole", back_populates="role")

    @property
    def users(self):
        return [user_role.user for user_role in self.user_roles]

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"


class UserRole(Base):
    """Table d'association pour la relation many-to-many entre User et Role."""

    __tablename__ = "user_roles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"), primary_key=True)

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
