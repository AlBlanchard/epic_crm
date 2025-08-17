from .base_crud import AbstractBaseCRUD  # Import relatif corrigé
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.user import User
from ..models.role import Role
from ..models.user_role import UserRole

ALLOWED_CREATE_FIELDS = {"username", "email", "employee_number"}
ALLOWED_UPDATE_FIELDS = {"username", "email", "employee_number"}


class UserCRUD(AbstractBaseCRUD):
    """CRUD operations pour la gestion des utilisateurs."""

    def __init__(self, session: Session):
        super().__init__(session)

    # ---------- CREATE ----------
    def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Crée un nouvel utilisateur.
        Note: pas de password_hash accepté ici. Le controller doit appeler user.set_password(...)
        pour gérer le password ici, pop 'password' et set_password().
        """
        payload = {k: v for k, v in user_data.items() if k in ALLOWED_CREATE_FIELDS}
        user = User(**payload)

        pwd = user_data.get("password")
        if pwd:
            user.set_password(pwd)

        try:
            self.session.add(user)
            self.session.commit()
            self.session.refresh(user)
            return user
        except IntegrityError as e:
            self.session.rollback()
            # duplicate key, etc.
            raise ValueError(
                f"Conflit d'unicité (username/email/employee_number): {e}"
            ) from e
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Erreur lors de la création de l'utilisateur: {e}") from e

    # ---------- READ ----------
    def get_all(
        self, filters: Optional[Dict[str, Any]] = None, order_by: Optional[str] = None
    ) -> List[User]:
        """Récupère tous les utilisateurs avec filtres et tri optionnels."""
        return self.get_entities(User, filters=filters, order_by=order_by)

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Récupère un utilisateur par son ID."""
        return self.session.get(User, user_id)

    def get_by_ids(self, user_ids: List[int]) -> List[User]:
        """Récupère plusieurs utilisateurs par leurs IDs."""
        return self.session.query(User).filter(User.id.in_(user_ids)).all()

    def find_by_username(self, username: str) -> Optional[User]:
        """Trouve un utilisateur par son nom d'utilisateur."""
        return self.session.query(User).filter_by(username=username).first()

    def find_by_email(self, email: str) -> Optional[User]:
        """Trouve un utilisateur par son email."""
        return self.session.query(User).filter_by(email=email).first()

    def get_users_by_role(self, role_name: str) -> List[User]:
        """Récupère tous les utilisateurs ayant un rôle spécifique."""
        return (
            self.session.query(User)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .filter(Role.name == role_name)
            .all()
        )

    def exists_by_username(self, username: str) -> bool:
        """Vérifie si un utilisateur existe avec ce nom d'utilisateur."""
        return self.session.query(User).filter_by(username=username).first() is not None

    def exists_by_email(self, email: str) -> bool:
        """Vérifie si un utilisateur existe avec cet email."""
        return self.session.query(User).filter_by(email=email).first() is not None

    def count_users(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Compte le nombre d'utilisateurs avec filtres optionnels."""
        query = self.session.query(User)
        if filters:
            for key, value in filters.items():
                if hasattr(User, key):
                    query = query.filter(getattr(User, key) == value)
        return query.count()

    # ---------- UPDATE ----------
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        user = self.session.get(User, user_id)
        if not user:
            return None

        # sécurité: n'autoriser que certains champs
        payload = {k: v for k, v in user_data.items() if k in ALLOWED_UPDATE_FIELDS}

        # password optionnel (hash via le modèle)
        pwd = user_data.get("password")
        if pwd:
            user.set_password(pwd)

        try:
            for key, value in payload.items():
                setattr(user, key, value)
            self.session.commit()
            self.session.refresh(user)
            return user
        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(
                f"Conflit d'unicité (username/email/employee_number): {e}"
            ) from e
        except Exception as e:
            self.session.rollback()
            raise ValueError(
                f"Erreur lors de la mise à jour de l'utilisateur: {e}"
            ) from e

    def update_password(self, user_id: int, raw_password: str) -> bool:
        user = self.session.get(User, user_id)
        if not user:
            return False
        try:
            user.set_password(raw_password)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise ValueError(
                f"Erreur lors de la mise à jour du mot de passe: {e}"
            ) from e

    # ---------- DELETE ----------
    def delete_user(self, user_id: int) -> bool:
        """
        Supprime un utilisateur.
        Note: Les vérifications métier sont faites par le controller.
        """
        user = self.session.get(User, user_id)
        if not user:
            return False

        try:
            self.session.delete(user)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise

    # ---------- ROLE MANAGEMENT ----------
    def add_role_to_user(self, user_id: int, role_id: int) -> bool:
        """Ajoute un rôle à un utilisateur."""
        # Vérifie que l'association n'existe pas déjà
        if self.user_has_role_by_id(user_id, role_id):
            return False

        try:
            user_role = UserRole(user_id=user_id, role_id=role_id)
            self.session.add(user_role)
            self.session.commit()
            return True
        except IntegrityError:
            self.session.rollback()
            return False
        except Exception as e:
            self.session.rollback()
            raise

    def remove_role_from_user(self, user_id: int, role_id: int) -> bool:
        """Retire un rôle d'un utilisateur."""
        user_role = (
            self.session.query(UserRole)
            .filter_by(user_id=user_id, role_id=role_id)
            .first()
        )

        if not user_role:
            return False

        try:
            self.session.delete(user_role)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise

    def get_user_roles(self, user_id: int) -> List[Role]:
        """Récupère tous les rôles d'un utilisateur."""
        return (
            self.session.query(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .filter(UserRole.user_id == user_id)
            .all()
        )

    def user_has_role_by_id(self, user_id: int, role_id: int) -> bool:
        """Vérifie si un utilisateur a un rôle spécifique (par ID)."""
        return (
            self.session.query(UserRole)
            .filter_by(user_id=user_id, role_id=role_id)
            .first()
            is not None
        )

    def user_has_role_by_name(self, user_id: int, role_name: str) -> bool:
        """Vérifie si un utilisateur a un rôle spécifique (par nom)."""
        return (
            self.session.query(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .filter(UserRole.user_id == user_id, Role.name == role_name)
            .first()
            is not None
        )

    def replace_user_roles(self, user_id: int, role_ids: List[int]) -> bool:
        """Remplace tous les rôles d'un utilisateur."""
        try:
            self.session.query(UserRole).filter_by(user_id=user_id).delete()

            for role_id in role_ids:
                user_role = UserRole(user_id=user_id, role_id=role_id)
                self.session.add(user_role)

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise
