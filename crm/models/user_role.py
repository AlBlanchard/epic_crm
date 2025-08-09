from sqlalchemy import (
    Integer,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..database import Base


class UserRole(Base):
    """Table d'association pour la relation many-to-many entre User et Role."""

    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"), primary_key=True
    )

    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"
