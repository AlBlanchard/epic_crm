from typing import Optional, Type, Dict, Callable, List
from functools import lru_cache
from .auth.auth import Authentication
from .auth.permission import Permission

from sqlalchemy.orm import Session

from .models.user import User
from .models.client import Client
from .models.contract import Contract
from .models.event import Event
from .models.role import Role


class DataReader:
    """
    Classe responsable de la lecture sécurisée des données métiers,
    en fonction des rôles de l'utilisateur connecté.
    """

    def __init__(self, session: Session, user_id: Optional[int] = None):
        self.session = session
        self._user_id = user_id
        self._current_user = None

    @property
    def current_user(self) -> User:
        """Lazy loading du current user avec cache."""
        if self._current_user is None:
            self._current_user = self._resolve_current_user()
        return self._current_user

    def _resolve_current_user(self) -> User:
        """Résout l'utilisateur courant depuis le token ou l'ID fourni."""
        if self._user_id:
            user = self.session.get(User, self._user_id)
            if not user:
                raise ValueError(f"Utilisateur {self._user_id} introuvable.")
            return user

        # Récupération depuis le token
        token = Authentication.load_token()
        if not token:
            raise ValueError("Aucun token trouvé. Veuillez vous connecter.")

        try:
            payload = Authentication.verify_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Token invalide.")

            user = self.session.get(User, user_id)
            if not user:
                raise ValueError("Utilisateur introuvable.")
            return user
        except Exception as e:
            raise PermissionError(f"Erreur d'authentification : {e}")

    def _get_entities(
        self,
        model: Type,
        permission_check: Callable[[User, Optional[int]], bool],
        owner_field: Optional[str] = None,
        user_id: Optional[int] = None,
        filters: Optional[Dict] = None,
        order_by: Optional[str] = None,
    ) -> List:
        """Fonction générique sécurisée pour récupérer des entités métiers."""

        # Vérification des permissions
        if not permission_check(self.current_user, user_id):
            raise PermissionError("Accès refusé : droits insuffisants.")

        query = self.session.query(model)

        # Filtrage par propriétaire
        if owner_field:
            id_to_use = user_id if user_id is not None else self.current_user.id
            query = query.filter(getattr(model, owner_field) == id_to_use)

        # Filtres additionnels
        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)

        # Tri
        if order_by and hasattr(model, order_by):
            query = query.order_by(getattr(model, order_by))

        return query.all()

    # API publique simplifiée
    def get_clients(self, user_id: Optional[int] = None, include_all: bool = False):
        """Récupère les clients selon les permissions."""
        owner_field = None if include_all else "sales_contact_id"
        return self._get_entities(
            model=Client,
            permission_check=Permission.has_permission,
            owner_field=owner_field,
            user_id=user_id,
            order_by="full_name",
        )

    def get_contracts(self, user_id: Optional[int] = None, include_all: bool = False):
        """Récupère les contrats selon les permissions."""
        owner_field = None if include_all else "sales_contact_id"
        return self._get_entities(
            model=Contract,
            permission_check=Permission.has_permission,
            owner_field=owner_field,
            user_id=user_id,
            order_by="created_at",
        )

    def get_events(self, user_id: Optional[int] = None, include_all: bool = False):
        """Récupère les événements selon les permissions."""
        owner_field = None if include_all else "support_contact_id"
        return self._get_entities(
            model=Event,
            permission_check=Permission.has_permission,
            owner_field=owner_field,
            user_id=user_id,
            order_by="date_start",
        )

    # Méthodes de commodité
    def get_my_clients(self):
        """Raccourci pour les clients de l'utilisateur connecté."""
        return self.get_clients(user_id=None, include_all=False)

    def get_all_clients(self):
        """Raccourci pour tous les clients (si autorisé)."""
        return self.get_clients(user_id=None, include_all=True)

    def get_my_contracts(self):
        """Raccourci pour les contrats de l'utilisateur connecté."""
        return self.get_contracts(user_id=None, include_all=False)

    def get_all_contracts(self):
        """Raccourci pour tous les contrats (si autorisé)."""
        return self.get_contracts(user_id=None, include_all=True)

    def get_my_events(self):
        """Raccourci pour les événements de l'utilisateur connecté."""
        return self.get_events(user_id=None, include_all=False)

    def get_all_events(self):
        """Raccourci pour tous les événements (si autorisé)."""
        return self.get_events(user_id=None, include_all=True)

    def get_all_users(self):
        """Récupère tous les utilisateurs (si l'utilisateur a les droits)."""
        if not Permission.is_admin(self.current_user):
            raise PermissionError("Accès refusé : droits insuffisants.")

        return self.session.query(User).all()

    def get_all_roles(self):
        """Récupère tous les rôles (si l'utilisateur a les droits)."""
        if not Permission.is_admin(self.current_user):
            raise PermissionError("Accès refusé : droits insuffisants.")

        return self.session.query(Role).all()
