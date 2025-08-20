from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from sqlalchemy import (
    Integer,
    String,
    Integer,
)
from sqlalchemy.orm import relationship, Session, Mapped, mapped_column
from .base import AbstractBase
from .role import Role
from .user_role import UserRole

ph = PasswordHasher(
    time_cost=3,  # nombre d'itérations
    memory_cost=65536,  # mémoire utilisée en KB (64MB ici)
    parallelism=4,  # threads
)


class User(AbstractBase):
    __tablename__ = "users"

    employee_number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relation many-tomany via la table d'association user_roles
    user_roles = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )

    clients = relationship("Client", back_populates="sales_contact")
    events = relationship("Event", back_populates="support_contact")

    @property
    def roles(self):
        return [user_role.role for user_role in self.user_roles]

    def set_password(self, raw_password: str) -> None:
        if not isinstance(raw_password, str) or not raw_password:
            raise ValueError("Le mot de passe ne peut pas être vide.")
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

    def has_role(self, role: "Role") -> bool:
        return any(user_role.role_id == role.id for user_role in self.user_roles)

    def add_role(self, role: "Role", session: "Session"):
        if role is None or session is None:
            raise ValueError("Le rôle et la session sont requis")

        if self.has_role(role):
            raise ValueError(
                f"L'utilisateur {self.username} a déjà le rôle {role.name}"
            )

        try:
            user_role = UserRole(user=self, role=role)
            session.add(user_role)
            session.flush()
            print(f"Rôle {role.name} ajouté à l'utilisateur {self.username}")

        except Exception as e:
            session.rollback()
            raise ValueError(f"Impossible d'ajouter le rôle : {str(e)}")

    def remove_role(self, role: "Role", session: "Session"):
        if role is None or session is None:
            raise ValueError("Le rôle et la session sont requis")

        user_role = next((ur for ur in self.user_roles if ur.role_id == role.id), None)

        if user_role is None:
            raise ValueError(
                f"L'utilisateur {self.username} n'a pas le rôle {role.name}"
            )

        try:
            session.delete(user_role)
            session.flush()
            print(f"Rôle {role.name} retiré de l'utilisateur {self.username}")

        except Exception as e:
            session.rollback()
            raise ValueError(f"Impossible de retirer le rôle : {str(e)}")

        def __repr__(self) -> str:
            role_names = ", ".join([role.name for role in self.roles])
            return (
                f"<User(id={self.id}, username='{self.username}', "
                f"employee_number={self.employee_number}, roles=[{role_names}])>"
            )
