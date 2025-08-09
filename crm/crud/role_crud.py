from .base_crud import AbstractBaseCRUD
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.role import Role
from ..models.user_role import UserRole
from ..models.user import User


class RoleCRUD(AbstractBaseCRUD):
    """CRUD operations pour la gestion des rôles."""

    def __init__(self, session: Session):
        super().__init__(session)

    # ---------- CREATE ----------
    def create_role(self, role_data: Dict) -> Role:
        """
        Crée un nouveau rôle.
        Note: La validation des données est faite par le controller.
        """
        try:
            role = Role(**role_data)
            self.session.add(role)
            self.session.commit()
            self.session.refresh(role)
            return role
        except IntegrityError as e:
            self.session.rollback()
            # Relance l'exception pour que le contrôleur puisse la gérer
            raise
        except Exception as e:
            self.session.rollback()
            raise

    # ---------- READ ----------
    def get_all(
        self, filters: Optional[Dict[str, Any]] = None, order_by: Optional[str] = None
    ) -> List[Role]:
        """Récupère tous les rôles avec filtres et tri optionnels."""
        return self.get_entities(Role, filters=filters, order_by=order_by)

    def get_by_id(self, role_id: int) -> Optional[Role]:
        """Récupère un rôle par son ID."""
        return self.session.get(Role, role_id)

    def find_by_name(self, name: str) -> Optional[Role]:
        """Trouve un rôle par son nom."""
        return self.session.query(Role).filter_by(name=name).first()

    def exists_by_name(self, name: str) -> bool:
        """Vérifie si un rôle existe avec ce nom."""
        return self.session.query(Role).filter_by(name=name).first() is not None

    def count_roles(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Compte le nombre de rôles avec filtres optionnels."""
        query = self.session.query(Role)
        if filters:
            for key, value in filters.items():
                if hasattr(Role, key):
                    query = query.filter(getattr(Role, key) == value)
        return query.count()

    # ---------- UPDATE ----------
    def update_role(self, role_id: int, role_data: Dict) -> Optional[Role]:
        """
        Met à jour un rôle existant.
        Note: La validation des données est faite par le controller.
        """
        role = self.session.get(Role, role_id)
        if not role:
            return None

        try:
            for key, value in role_data.items():
                if hasattr(role, key):  # Sécurité basique
                    setattr(role, key, value)

            self.session.commit()
            self.session.refresh(role)
            return role
        except IntegrityError as e:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise

    # ---------- DELETE ----------
    def delete_role(self, role_id: int) -> bool:
        """
        Supprime un rôle.
        Note: Les vérifications métier sont faites par le controller.
        """
        role = self.session.get(Role, role_id)
        if not role:
            return False

        try:
            self.session.delete(role)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise

    # ---------- USER MANAGEMENT ----------
    def get_users_with_role(self, role_id: int) -> List[User]:
        """Récupère tous les utilisateurs ayant un rôle spécifique."""
        return (
            self.session.query(User)
            .join(UserRole, User.id == UserRole.user_id)
            .filter(UserRole.role_id == role_id)
            .all()
        )

    def get_users_with_role_by_name(self, role_name: str) -> List[User]:
        """Récupère tous les utilisateurs ayant un rôle spécifique (par nom)."""
        return (
            self.session.query(User)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, Role.id == UserRole.role_id)
            .filter(Role.name == role_name)
            .all()
        )

    def count_users_with_role(self, role_id: int) -> int:
        """Compte le nombre d'utilisateurs ayant un rôle spécifique."""
        return self.session.query(UserRole).filter_by(role_id=role_id).count()

    def role_is_assigned(self, role_id: int) -> bool:
        """Vérifie si un rôle est assigné à au moins un utilisateur."""
        return self.count_users_with_role(role_id) > 0

    def add_user_to_role(self, role_id: int, user_id: int) -> bool:
        """Ajoute un utilisateur à un rôle."""
        try:
            user_role = UserRole(user_id=user_id, role_id=role_id)
            self.session.add(user_role)
            self.session.commit()
            return True
        except IntegrityError:
            # Association déjà existante
            self.session.rollback()
            return False
        except Exception as e:
            self.session.rollback()
            raise

    def remove_user_from_role(self, role_id: int, user_id: int) -> bool:
        """Retire un utilisateur d'un rôle."""
        user_role = (
            self.session.query(UserRole)
            .filter_by(role_id=role_id, user_id=user_id)
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

    def replace_role_users(self, role_id: int, user_ids: List[int]) -> bool:
        """Remplace tous les utilisateurs d'un rôle."""
        try:
            # Supprimer toutes les associations actuelles pour ce rôle
            self.session.query(UserRole).filter_by(role_id=role_id).delete()

            # Ajouter les nouveaux utilisateurs
            for user_id in user_ids:
                user_role = UserRole(user_id=user_id, role_id=role_id)
                self.session.add(user_role)

            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise

    # ---------- UTILITY METHODS ----------
    def get_default_roles(self) -> List[Role]:
        """Récupère les rôles par défaut du système (admin, sales, support)."""
        default_role_names = ["admin", "sales", "support"]
        return self.session.query(Role).filter(Role.name.in_(default_role_names)).all()

    def role_exists_by_id(self, role_id: int) -> bool:
        """Vérifie si un rôle existe par son ID."""
        return self.session.get(Role, role_id) is not None

    def get_role_stats(self, role_id: int) -> Dict[str, Any]:
        """Récupère les statistiques d'un rôle."""
        role = self.session.get(Role, role_id)
        if not role:
            return {}

        user_count = self.count_users_with_role(role_id)

        return {
            "role_id": role_id,
            "role_name": role.name,
            "user_count": user_count,
            "is_assigned": user_count > 0,
            "created_at": getattr(role, "created_at", None),
            "updated_at": getattr(role, "updated_at", None),
        }
