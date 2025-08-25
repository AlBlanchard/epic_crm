from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import SessionLocal
from datetime import datetime
from ..auth.auth import Authentication
from ..crud.user_crud import UserCRUD
from ..models.user import User
from ..auth.permission import Permission


class AbstractController(ABC):
    """
    Contrôleur de base très léger :
    - gère la session (injection, context manager),
    - point d'extension pour connecter les services/CRUD.
    """

    def __init__(self, session: Optional[Session] = None):
        self.session = session or SessionLocal()
        self.user_crud = UserCRUD(self.session)
        self._owns_session = session is None
        self._setup_services()

    @abstractmethod
    def _setup_services(self) -> None:
        """Initialise les services/CRUD spécifiques du contrôleur."""
        pass

    def _get_current_user(self) -> User:
        token = Authentication.load_token()
        if not token:
            raise PermissionError("Non authentifié.")
        payload = Authentication.verify_token(token)
        me = self.user_crud.get_by_id(int(payload["sub"]))
        if not me:
            raise PermissionError("Utilisateur courant introuvable.")
        return me

    def _ensure_admin(self, me: User) -> None:
        if not Permission.is_admin(me):
            raise PermissionError("Accès refusé : administrateur requis.")

    def _ensure_owner_or_admin(self, me: User, owner_id: int) -> None:
        if not (Permission.is_admin(me) or me.id == owner_id):
            raise PermissionError("Accès refusé.")
