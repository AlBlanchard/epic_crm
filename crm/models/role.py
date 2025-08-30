from sqlalchemy import (
    Integer,
    String,
    Integer,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..database import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    user_roles = relationship("UserRole", back_populates="role")

    @property
    def users(self):
        return [user_role.user for user_role in self.user_roles]

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"

    try:
        from ..tests.conftest import TestingBase as BaseForTests
    except ImportError:
        from .base import AbstractBase as BaseForTests
