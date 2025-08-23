from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import SessionLocal
from datetime import datetime


class AbstractController(ABC):
    """
    Contrôleur de base très léger :
    - gère la session (injection, context manager),
    - point d'extension pour connecter les services/CRUD.
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

    def ensure_datetime(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Impossible de convertir {value!r} en datetime")
        raise ValueError(f"Type non supporté: {type(value)}")
