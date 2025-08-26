import re

from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    Integer,
    CheckConstraint,
    case,
)
from sqlalchemy.orm import relationship, validates, Mapped, mapped_column
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import select

from ..models.user import User
from ..utils.validations import Validations

from .base import AbstractBase


class Client(AbstractBase):
    __tablename__ = "clients"
    __table_args__ = (CheckConstraint("email != ''", name="check_client_email"),)

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(15))
    company_name: Mapped[str] = mapped_column(String(200))

    # Many Client to One User
    sales_contact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    sales_contact = relationship("User", back_populates="clients")
    contracts = relationship("Contract", back_populates="client")

    # Permet de faire des recherches SQL sur des champs propriétés (filtre, etc...)
    # Doit garder le même nom que l'expression ci-dessous, ignore sinon l'IDE râle.
    @hybrid_property
    def sales_contact_name(self):  # type: ignore
        return self.sales_contact.username if self.sales_contact else "Aucun contact"

    @sales_contact_name.expression
    def sales_contact_name(cls):
        return (
            select(User.username)
            .where(User.id == cls.sales_contact_id)
            .correlate(cls)
            .scalar_subquery()
        )

    @hybrid_property
    def is_assigned(self):  # type: ignore
        return self.sales_contact is not None

    @is_assigned.expression
    def is_assigned(cls):
        return case({cls.sales_contact_id != None: True}, else_=False).label(
            "is_assigned"
        )

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.full_name}')>"

    @validates("email")
    def validate_email(self, key, value):
        Validations.validate_email(value)
        return value

    @validates("phone")
    def validate_phone(self, key, value):
        Validations.validate_phone(value)

        return value
