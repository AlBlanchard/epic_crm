from typing import Any, Dict, List, Iterable, Optional
from crm.models.event import Event


class EventSerializer:
    PUBLIC_FIELDS = {
        "id",
        "contract_id",
        "support_contact_id",
        "date_start",
        "date_end",
        "location",
        "attendees",
        "notes",
        "created_at",
        "updated_at",
    }

    def __init__(self, *, fields: Optional[Iterable[str]] = None):
        self.fields = set(fields) if fields else set(self.PUBLIC_FIELDS)

    @staticmethod
    def _to_iso(v: Any) -> Any:
        return v.isoformat() if hasattr(v, "isoformat") else v

    def serialize(
        self, event: Event, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if event is None:
            return {}
        data: Dict[str, Any] = {}
        for col in event.__table__.columns:
            name = col.name
            if name in self.fields:
                data[name] = self._to_iso(getattr(event, name))
        if extra:
            data.update(extra)
        return data

    def serialize_list(self, events: List[Event]) -> List[Dict[str, Any]]:
        return [self.serialize(e) for e in events]
