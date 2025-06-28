from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as PgEnum
from .database import Base
import datetime


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    sales_contact_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount_total = Column(Numeric(10, 2), nullable=False)
    amount_due = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    is_signed = Column(Boolean, default=False)

    client = relationship("Client", back_populates="contracts")
    sales_contact = relationship("User", back_populates="contracts")
    event = relationship("Event", back_populates="contract", uselist=False)

    def __repr__(self) -> str:
        return f"<Contract(id={self.id}, total={self.amount_total}, signed={self.is_signed})>"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    # One to one avec Contract, pour faire un Many Event to One Contract, enlever le unique=True
    contract_id = Column(Integer, ForeignKey("contracts.id"), unique=True)
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


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
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


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String)
    company_name = Column(String)
    first_contact = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc)
    )
    last_contact = Column(
        DateTime, default=datetime.datetime.now(datetime.timezone.utc)
    )
    # Many Client to One User
    sales_contact_id = Column(Integer, ForeignKey("users.id"))

    sales_contact = relationship("User", back_populates="clients")
    contracts = relationship("Contract", back_populates="client")


def __repr__(self) -> str:
    return f"<Client(id={self.id}, name='{self.full_name}')>"
