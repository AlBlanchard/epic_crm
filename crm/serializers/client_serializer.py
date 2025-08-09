from typing import Any, Dict, List, Iterable, Optional
from crm.models.client import Client


class ClientSerializer:
    PUBLIC_FIELDS = {
        "id",
        "full_name",
        "email",
        "phone",
        "company_name",
        "sales_contact_id",
        "created_at",
        "updated_at",
    }

    def __init__(self, *, fields: Optional[Iterable[str]] = None):
        self.fields = set(fields) if fields else set(self.PUBLIC_FIELDS)

    @staticmethod
    def _to_iso(v: Any) -> Any:
        return v.isoformat() if hasattr(v, "isoformat") else v

    def serialize(
        self, client: Client, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if client is None:
            return {}
        data: Dict[str, Any] = {}
        for col in client.__table__.columns:
            name = col.name
            if name in self.fields:
                data[name] = self._to_iso(getattr(client, name))
        if extra:
            data.update(extra)
        return data

    def serialize_list(self, clients: List[Client]) -> List[Dict[str, Any]]:
        return [self.serialize(c) for c in clients]
