# crm/serializers/user_serializer.py
from typing import Any, Dict, List, Iterable, Optional
from crm.models.user import User
from ..utils.validations import Validations


class UserSerializer:
    """Sérialise les objets User sans exposer le mot de passe."""

    PUBLIC_USER_FIELDS = {
        "id",
        "employee_number",
        "username",
        "email",
        "created_at",
        "updated_at",
        "roles",
    }

    def __init__(
        self, *, fields: Optional[Iterable[str]] = None, include_roles: bool = True
    ):
        """
        Args:
            fields: Liste des champs à exposer (défaut: PUBLIC_USER_FIELDS)
            include_roles: Inclure la clé 'roles' (liste de noms) si True
        """
        self.fields = set(fields) if fields else set(self.PUBLIC_USER_FIELDS)
        self.include_roles = include_roles
        self.valid = Validations()

    @staticmethod
    def _to_iso(value: Any) -> Any:
        """Convertit datetime/date en ISO 8601 si applicable."""
        return value.isoformat() if hasattr(value, "isoformat") else value

    @staticmethod
    def _extract_roles_from_user_roles(user: "User") -> List[str]:
        """Récupère les noms des rôles via la relation user.user_roles -> role."""
        names: List[str] = []
        user_roles = getattr(user, "user_roles", None)
        if user_roles:
            for ur in user_roles:
                role = getattr(ur, "role", None)
                if role is not None:
                    names.append(getattr(role, "name", str(role)))
        return names

    def serialize(
        self, user: User, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if user is None:
            return {}

        data: Dict[str, Any] = {}

        # Colonnes SQL whitelistees
        for col in user.__table__.columns:
            name = col.name
            if name in {"password", "password_hash"}:
                continue
            if name in self.fields:
                # Validations
                if name == "email":
                    self.valid.validate_email(getattr(user, name))
                if name == "employee_number":
                    self.valid.validate_int_max_length(getattr(user, name))
                if name == "username":
                    self.valid.validate_str_max_length(getattr(user, name))
                data[name] = self._to_iso(getattr(user, name))

        # Champ calculé roles (via user_roles/role)
        if self.include_roles and "roles" in self.fields:
            data["roles"] = self._extract_roles_from_user_roles(user)

        if extra:
            data.update(extra)

        return data

    def serialize_list(self, users: List["User"]) -> List[Dict[str, Any]]:
        return [self.serialize(u) for u in users if u is not None]
