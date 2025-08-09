from .base_crud import AbstractBaseCRUD
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.event import Event
from datetime import datetime


class EventCRUD(AbstractBaseCRUD):
    """CRUD operations basiques pour les événements."""

    def __init__(self, session: Session):
        super().__init__(session)

    # ---------- CREATE ----------
    def create(self, event_data: Dict) -> Event:
        """Crée un nouvel événement."""
        try:
            event = Event(**event_data)
            self.session.add(event)
            self.session.commit()
            self.session.refresh(event)
            return event
        except IntegrityError:
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            raise

    # ---------- READ ----------
    def get_all(
        self, filters: Optional[Dict[str, Any]] = None, order_by: Optional[str] = None
    ) -> List[Event]:
        """Récupère tous les événements avec filtres optionnels."""
        return self.get_entities(Event, filters=filters, order_by=order_by)

    def get_by_id(self, event_id: int) -> Optional[Event]:
        """Récupère un événement par son ID."""
        return self.session.get(Event, event_id)

    def get_by_contract(self, contract_id: int) -> List[Event]:
        """Récupère les événements d'un contrat."""
        return self.session.query(Event).filter_by(contract_id=contract_id).all()

    def get_by_support_contact(self, support_contact_id: int) -> List[Event]:
        """Récupère les événements d'un support."""
        return (
            self.session.query(Event)
            .filter_by(support_contact_id=support_contact_id)
            .all()
        )

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Event]:
        """Récupère les événements dans une plage de dates."""
        return (
            self.session.query(Event)
            .filter(Event.date_start >= start_date)
            .filter(Event.date_start <= end_date)
            .all()
        )

    # ---------- UPDATE ----------
    def update(self, event_id: int, event_data: Dict) -> Optional[Event]:
        """Met à jour un événement."""
        event = self.session.get(Event, event_id)
        if not event:
            return None

        try:
            for key, value in event_data.items():
                if hasattr(event, key):
                    setattr(event, key, value)
            self.session.commit()
            self.session.refresh(event)
            return event
        except IntegrityError:
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            raise

    # ---------- DELETE ----------
    def delete(self, event_id: int) -> bool:
        """Supprime un événement."""
        event = self.session.get(Event, event_id)
        if not event:
            return False

        try:
            self.session.delete(event)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    # ---------- UTILITY ----------
    def exists(self, event_id: int) -> bool:
        """Vérifie si un événement existe."""
        return self.session.get(Event, event_id) is not None

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Compte les événements avec filtres optionnels."""
        query = self.session.query(Event)
        if filters:
            for key, value in filters.items():
                if hasattr(Event, key):
                    query = query.filter(getattr(Event, key) == value)
        return query.count()
