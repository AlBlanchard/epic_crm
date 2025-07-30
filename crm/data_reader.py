from typing import Optional, Type
from .auth.auth import Authentication
from auth.jti_manager import JTIManager
from .auth.permission import Permission
from crm.models import User, Client, Contract, Event
from sqlalchemy.orm import Session


class DataReader:
    """
    Classe responsable de la lecture sécurisée des données métiers,
    en fonction des rôles de l'utilisateur connecté.
    """

    def __init__(self, session: Session):
        self.session = session
        self.current_user = self._get_current_user()

    def _get_current_user(self) -> User:
        token = Authentication.load_token()
        if not token:
            raise ValueError("Aucun token trouvé. Veuillez vous connecter.")

        payload = Authentication.verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Token invalide.")

        user = self.session.get(User, user_id)
        if not user:
            raise ValueError("Utilisateur introuvable.")
        return user

    def _get_entities(
        self,
        model: Type,
        permission_check,
        owner_field: Optional[str] = None,
        user_id: Optional[int] = None,
    ):
        """
        Fonction générique sécurisée pour récupérer des entités métiers.

        - model: classe SQLAlchemy (Client, Contract, etc.)
        - permission_check: fonction de la classe Permission à appeler (ex: Permission.can_view_clients)
        - owner_field: champ à filtrer si on cible un user spécifique
        - user_id: None pour l’utilisateur connecté, ou ID d’un autre utilisateur (admin only)
        """
        if not permission_check(self.current_user, user_id):
            raise PermissionError(
                "Accès refusé : vous n'avez pas les droits suffisants."
            )

        query = self.session.query(model)

        if owner_field:
            id_to_use = user_id if user_id is not None else self.current_user.id
            query = query.filter(getattr(model, owner_field) == id_to_use)

        return query.all()

    # Méthodes publiques sécurisées avec Permission

    def get_clients_for(self, user_id: Optional[int] = None):
        return self._get_entities(
            model=Client,
            permission_check=Permission.can_view_clients,
            owner_field="sales_contact_id",
            user_id=user_id,
        )

    def get_contracts_for(self, user_id: Optional[int] = None):
        return self._get_entities(
            model=Contract,
            permission_check=Permission.can_view_contracts,
            owner_field="sales_contact_id",
            user_id=user_id,
        )

    def get_events_for(self, user_id: Optional[int] = None):
        return self._get_entities(
            model=Event,
            permission_check=Permission.can_view_events,
            owner_field="support_contact_id",
            user_id=user_id,
        )

    def get_all_clients(self):
        return self._get_entities(
            model=Client, permission_check=Permission.can_view_clients
        )

    def get_all_contracts(self):
        return self._get_entities(
            model=Contract, permission_check=Permission.can_view_contracts
        )

    def get_all_events(self):
        return self._get_entities(
            model=Event, permission_check=Permission.can_view_events
        )

    def get_my_clients(self):
        return self._get_entities(
            model=Client,
            permission_check=Permission.can_view_clients,
            owner_field="sales_contact_id",
        )

    def get_my_contracts(self):
        return self._get_entities(
            model=Contract,
            permission_check=Permission.can_view_contracts,
            owner_field="sales_contact_id",
        )

    def get_my_events(self):
        return self._get_entities(
            model=Event,
            permission_check=Permission.can_view_events,
            owner_field="support_contact_id",
        )
