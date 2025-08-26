from typing import Any, Dict, List, Iterable, Optional
from crm.models.client import Client
from crm.utils.validations import Validations


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

    # Tous les champs calculés
    COMPUTED_FIELDS = {
        "sales_contact_name": lambda c: (
            c.sales_contact_name if c.sales_contact else "Aucun contact"
        ),
    }

    def __init__(self, *, fields: Optional[Iterable[str]] = None):
        if fields is None:
            self.fields = set(self.PUBLIC_FIELDS) | set(
                self.COMPUTED_FIELDS.keys()
            )  # Initialise les deux fields
            self.valid = Validations()
        else:
            self.fields = set(fields)
            self.valid = Validations()

    @staticmethod
    def _to_iso(v: Any) -> Any:
        return v.isoformat() if hasattr(v, "isoformat") else v

    def serialize(
        self, client: Client, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if client is None:
            return {}
        data: Dict[str, Any] = {}

        # Colonnes SQL
        for col in client.__table__.columns:
            name = col.name
            if name in self.fields:
                data[name] = self._to_iso(getattr(client, name))

        # Champs calculés
        for name, getter in self.COMPUTED_FIELDS.items():
            if name in self.fields:
                # Validations
                if name == "email":
                    self.valid.validate_email(getattr(client, name))
                if name == "phone":
                    self.valid.validate_phone(getattr(client, name))
                if name == "company_name":
                    self.valid.validate_str_max_length(
                        getattr(client, name), max_length=200
                    )
                if name == "full_name":
                    self.valid.validate_str_max_length(getattr(client, name))

                try:
                    value = getter(client)
                except Exception as e:
                    value = None

                if value is None:
                    value = "Aucun"

                data[name] = self._to_iso(value)

        if extra:
            data.update(extra)
        return data

    def serialize_list(self, clients: List[Client]) -> List[Dict[str, Any]]:
        return [self.serialize(c) for c in clients]
