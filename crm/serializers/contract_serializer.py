from typing import Any, Dict, List, Iterable, Optional
from crm.models.contract import Contract


class ContractSerializer:
    PUBLIC_FIELDS = {
        "id",
        "client_id",
        "amount_total",
        "amount_due",
        "is_signed",
        "created_at",
        "updated_at",
    }

    COMPUTED_FIELDS = {
        "sales_contact_name": lambda c: (
            c.sales_contact_name if c.sales_contact_name else "Aucun contact"
        ),
        "client_name": lambda c: c.client_name,
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
        return v.isoformat() if hasattr(v, "isoformat") else v

    def serialize(
        self, contract: Contract, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if contract is None:
            return {}
        data: Dict[str, Any] = {}

        # Colonnes SQL
        for col in contract.__table__.columns:
            name = col.name
            if name in self.fields:
                data[name] = self._to_iso(getattr(contract, name))

        # Champs calculés
        for name, getter in self.COMPUTED_FIELDS.items():
            if name in self.fields:
                data[name] = self._to_iso(getter(contract))

        if extra:
            data.update(extra)
        return data

    def serialize_list(self, contracts: List[Contract]) -> List[Dict[str, Any]]:
        return [self.serialize(c) for c in contracts]
