from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as PgEnum
from .database import Base
import datetime


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

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String)
    company_name = Column(String)
    first_contact = Column(DateTime, default=datetime.datetime.utcnow)
    last_contact = Column(DateTime, default=datetime.datetime.utcnow)
    sales_contact_id = Column(Integer, ForeignKey("users.id"))

    sales_contact = relationship("User", back_populates="clients")


def __repr__(self) -> str:
    return f"<Client(id={self.id}, name='{self.full_name}')>"
