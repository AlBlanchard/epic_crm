from argon2 import PasswordHasher

from sqlalchemy import (
    Integer,
    ForeignKey,
    Numeric,
    Boolean,
    Integer,
)
from sqlalchemy.orm import relationship, validates, Mapped, mapped_column
from sqlalchemy import CheckConstraint
from .base import AbstractBase
from decimal import Decimal


class Contract(AbstractBase):
    __tablename__ = "contracts"
    __table_args__ = (
        CheckConstraint("amount_due <= amount_total", name="check_amount_due"),
    )

    client_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False
    )

    amount_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    client = relationship("Client", back_populates="contracts")
    event = relationship("Event", back_populates="contract", uselist=False)

    @property
    def client_name(self):
        return self.client.full_name

    @property
    def sales_contact_name(self):
        return (
            self.client.sales_contact.username
            if self.client.sales_contact
            else "Aucun contact"
        )

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
