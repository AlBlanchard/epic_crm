# crm/controllers/base.py
from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import SessionLocal


class AbstractController(ABC):
    """
    Contrôleur de base très léger :
    - gère la session (injection, context manager),
    - point d’extension pour connecter les services/CRUD.
    """

    def __init__(self, session: Optional[Session] = None):
        self.session = session or SessionLocal()
        self._owns_session = session is None
        self._setup_services()

    @abstractmethod
    def _setup_services(self) -> None:
        """Initialise les services/CRUD spécifiques du contrôleur."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._owns_session and self.session:
            self.session.close()

    # Optionnel : mapper proprement des erreurs DB en exceptions métier
    def _db_guard(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except IntegrityError as e:
            # à toi de lever/mapper une exception métier
            raise ValueError("Conflit d'unicité ou intégrité") from e
