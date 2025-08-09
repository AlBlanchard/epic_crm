from typing import Any, Dict, List, Iterable, Optional
from crm.models.contract import Contract


class ContractSerializer:
    PUBLIC_FIELDS = {
        "id",
        "client_id",
        "sales_contact_id",
        "amount_total",
        "amount_due",
        "is_signed",
        "created_at",
        "updated_at",
    }

    def __init__(self, *, fields: Optional[Iterable[str]] = None):
        self.fields = set(fields) if fields else set(self.PUBLIC_FIELDS)

    @staticmethod
    def _to_iso(v: Any) -> Any:
        return v.isoformat() if hasattr(v, "isoformat") else v

    def serialize(
        self, contract: Contract, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if contract is None:
            return {}
        data: Dict[str, Any] = {}
        for col in contract.__table__.columns:
            name = col.name
            if name in self.fields:
                data[name] = self._to_iso(getattr(contract, name))
        if extra:
            data.update(extra)
        return data

    def serialize_list(self, contracts: List[Contract]) -> List[Dict[str, Any]]:
        return [self.serialize(c) for c in contracts]
