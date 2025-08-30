from sqlalchemy import (
    Integer,
    ForeignKey,
    Numeric,
    Boolean,
    Integer,
)
from sqlalchemy.orm import relationship, validates, Mapped, mapped_column, aliased
from sqlalchemy import CheckConstraint, case
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql import select


from .base import AbstractBase
from decimal import Decimal
from ..models.client import Client
from ..models.user import User


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

    # Type ignore car l'IDE ne comprend pas qu'ils doivent avoir le même nom
    @hybrid_property
    def client_name(self):  # type: ignore
        return self.client.full_name

    @client_name.expression
    def client_name(cls):
        return (
            select(Client.full_name)
            .where(Client.id == cls.client_id)
            .correlate(cls)
            .scalar_subquery()
        )

    @hybrid_property
    def sales_contact_name(self):  # type: ignore
        return (
            self.client.sales_contact.username
            if self.client.sales_contact
            else "Aucun contact"
        )

    @sales_contact_name.expression
    def sales_contact_name(cls):
        ClientAlias = aliased(Client)
        return (
            select(User.username)
            .join(ClientAlias, ClientAlias.sales_contact_id == User.id)
            .where(ClientAlias.id == cls.client_id)
            .correlate(cls)
            .scalar_subquery()
        )

    @hybrid_property
    def sales_contact_id(self):  # type: ignore
        return self.client.sales_contact_id if self.client else None

    @sales_contact_id.expression
    def sales_contact_id(cls):
        ClientAlias = aliased(Client)
        return (
            select(ClientAlias.sales_contact_id)
            .where(ClientAlias.id == cls.client_id)
            .correlate(cls)
            .scalar_subquery()
        )

    @hybrid_property
    def is_payed(self):  # type: ignore
        return self.amount_due == 0

    @is_payed.expression
    def is_payed(cls):
        return case({cls.amount_due == 0: True}, else_=False).label("is_payed")

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

    try:
        from ..tests.conftest import TestingBase as BaseForTests
    except ImportError:
        from .base import AbstractBase as BaseForTests
