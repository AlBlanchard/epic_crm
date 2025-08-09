# crm/serializers/user_serializer.py
from typing import Any, Dict, List, Iterable, Optional
from crm.models.user import User


class UserSerializer:
    """Sérialise les objets User sans exposer le mot de passe."""

    PUBLIC_USER_FIELDS = {
        "id",
        "employee_number",
        "username",
        "email",
        "created_at",
        "updated_at",
    }

    def __init__(
        self, *, fields: Optional[Iterable[str]] = None, include_roles: bool = True
    ):
        """
        Args:
            fields: Liste des champs à exposer (défaut: PUBLIC_USER_FIELDS)
            include_roles: Inclure ou non les rôles dans la sortie
        """
        self.fields = set(fields) if fields else self.PUBLIC_USER_FIELDS
        self.include_roles = include_roles

    @staticmethod
    def _to_iso(value: Any) -> Any:
        """Convertit datetime/date en ISO 8601 si applicable."""
        return value.isoformat() if hasattr(value, "isoformat") else value

    def serialize(
        self, user: User, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sérialise un utilisateur.
        Args:
            user: instance User SQLAlchemy
            extra: dict fusionné au résultat (ex: infos calculées)
        """
        if user is None:
            return {}

        data: Dict[str, Any] = {}
        for col in user.__table__.columns:
            name = col.name
            if name == "password_hash":
                continue
            if name in self.fields:
                data[name] = self._to_iso(getattr(user, name))

        if self.include_roles:
            data["roles"] = [r.name for r in getattr(user, "roles", [])]

        if extra:
            data.update(extra)

        return data

    def serialize_list(self, users: List[User]) -> List[Dict[str, Any]]:
        """Sérialise une liste d'utilisateurs."""
        return [self.serialize(u) for u in users]
