from .base_crud import AbstractBaseCRUD
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.role import Role


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
                if hasattr(role, key):
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
