from typing import Any, Dict, List, Iterable, Optional
from crm.models.event import Event, EventNote


class EventSerializer:
    PUBLIC_FIELDS = {
        "id",
        "contract_id",
        "support_contact_id",
        "date_start",
        "date_end",
        "location",
        "attendees",
        "created_at",
        "updated_at",
    }

    COMPUTED_FIELDS = {
        "client_name": lambda event: event.contract.client_name,
        "client_contact": lambda event: [
            event.contract.client.email,
            event.contract.client.phone,
        ],
        "support_contact_name": lambda event: event.support_contact.username,
        "notes": lambda event: [note.note for note in event.notes],
    }

    def __init__(self, *, fields: Optional[Iterable[str]] = None):
        if fields is None:
            self.fields = set(self.PUBLIC_FIELDS) | set(
                self.COMPUTED_FIELDS.keys()
            )  # Initialise les deux fields
        else:
            self.fields = set(fields)

    @staticmethod
    def _to_iso(v: Any) -> Any:
        # version récursive pour listes/dicts + datetimes
        if hasattr(v, "isoformat"):
            return v.isoformat()
        if isinstance(v, list):
            return [EventSerializer._to_iso(x) for x in v]
        if isinstance(v, dict):
            return {k: EventSerializer._to_iso(x) for k, x in v.items()}
        return v

    def serialize(
        self, event: Event, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if event is None:
            return {}
        data: Dict[str, Any] = {}

        # Colonnes SQL
        for col in event.__table__.columns:
            name = col.name
            if name in self.fields:
                data[name] = self._to_iso(getattr(event, name))

        # Champs calculés
        for name, getter in self.COMPUTED_FIELDS.items():
            if name in self.fields:
                try:
                    value = getter(event)
                except Exception as e:
                    value = None

                if value is None:
                    value = "Aucun"

                data[name] = self._to_iso(value)

        if extra:
            data.update(extra)

        return data

    def serialize_list(self, events: List[Event]) -> List[Dict[str, Any]]:
        return [self.serialize(e) for e in events]


class EventNoteSerializer:
    PUBLIC_FIELDS = {
        "id",
        "event_id",
        "note",
        "created_at",
    }

    def __init__(self, *, fields: Optional[Iterable[str]] = None):
        if fields is None:
            self.fields = set(self.PUBLIC_FIELDS)
        else:
            self.fields = set(fields)

    @staticmethod
    def _to_iso(v: Any) -> Any:
        # version récursive pour listes/dicts + datetimes
        if hasattr(v, "isoformat"):
            return v.isoformat()
        if isinstance(v, list):
            return [EventNoteSerializer._to_iso(x) for x in v]
        if isinstance(v, dict):
            return {k: EventNoteSerializer._to_iso(x) for k, x in v.items()}
        return v

    def serialize(self, note: EventNote) -> Dict[str, Any]:
        if note is None:
            return {}
        data: Dict[str, Any] = {}

        # Colonnes SQL
        for col in note.__table__.columns:
            name = col.name
            if name in self.fields:
                data[name] = self._to_iso(getattr(note, name))

        return data

    def serialize_list(self, notes: List[EventNote]) -> List[Dict[str, Any]]:
        return [self.serialize(n) for n in notes]
