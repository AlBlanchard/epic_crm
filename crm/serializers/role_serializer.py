from typing import Any, Dict, List, Iterable, Optional
from crm.models.role import Role


class RoleSerializer:
    PUBLIC_FIELDS = {"id", "name", "created_at", "updated_at"}

    def __init__(self, *, fields: Optional[Iterable[str]] = None):
        self.fields = set(fields) if fields else set(self.PUBLIC_FIELDS)

    @staticmethod
    def _to_iso(v: Any) -> Any:
        return v.isoformat() if hasattr(v, "isoformat") else v

    def serialize(
        self, role: Role, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if role is None:
            return {}
        data: Dict[str, Any] = {}
        for col in role.__table__.columns:
            name = col.name
            if name in self.fields:
                data[name] = self._to_iso(getattr(role, name))
        if extra:
            data.update(extra)
        return data

    def serialize_list(self, roles: List[Role]) -> List[Dict[str, Any]]:
        return [self.serialize(r) for r in roles]
