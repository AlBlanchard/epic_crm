from .base_crud import AbstractBaseCRUD
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.event import Event
from ..models.event import EventNote
from ..models.contract import Contract
from sqlalchemy.orm import Session, selectinload


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

    def create_note(self, note_data: Dict) -> EventNote:
        """Crée une nouvelle note pour un événement."""
        try:
            note = EventNote(**note_data)
            self.session.add(note)
            self.session.commit()
            self.session.refresh(note)
            return note
        except IntegrityError:
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            raise

    # ---------- READ ----------
    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Event]:
        """Récupère tous les contrats avec filtres/tri et eager-load anti-N+1."""
        return self.get_entities(
            Event,
            filters=filters,
            order_by=order_by,
            limit=limit,
            offset=offset,
            eager_options=(
                # N+1
                selectinload(Event.contract),
                selectinload(Event.notes),
                selectinload(Event.support_contact),
                # N+2
                selectinload(Event.contract).selectinload(Contract.client),
            ),
        )

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

    def get_notes(self, event_id: int) -> List[EventNote]:
        """Récupère les notes d'un événement."""
        return self.session.query(EventNote).filter_by(event_id=event_id).all()

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

    def delete_note(self, note_id: int) -> bool:
        """Supprime une note d'événement."""
        note = self.session.get(EventNote, note_id)
        if not note:
            return False

        try:
            self.session.delete(note)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise
