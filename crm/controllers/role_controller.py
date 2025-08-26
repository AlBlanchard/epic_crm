from typing import Dict, Any, Optional, List
from .base import AbstractController
from ..crud.role_crud import RoleCRUD
from ..crud.user_crud import UserCRUD
from ..serializers.user_serializer import UserSerializer
from ..serializers.role_serializer import RoleSerializer
from ..auth.permission import Permission


class RoleController(AbstractController):
    """Logique métier pour Roles : admin-only pour la gestion."""

    def _setup_services(self) -> None:
        self.roles = RoleCRUD(self.session)
        self.users = UserCRUD(self.session)
        self.role_serializer = RoleSerializer()
        self.user_serializer = UserSerializer()

    # ---------- Read ----------
    def list_roles(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()

        if not Permission.read_permission(me, "user"):
            raise ValueError("Accès refusé.")
        rows = self.roles.get_all(filters=filters, order_by=order_by)

        if not Permission.is_admin(me):
            # Ne montre pas le rôle admin aux non-admins
            rows = [role for role in rows if role.name != "admin"]

        return self.role_serializer.serialize_list(rows)

    def get_role(self, role_id: int) -> Dict[str, Any]:
        me = self._get_current_user()
        if not Permission.read_permission(me, "user"):
            raise ValueError("Accès refusé.")

        if not Permission.is_admin(me):
            # Ne montre pas le rôle admin aux non-admins
            role = self.roles.get_by_id(role_id)
            if role and role.name == "admin":
                raise ValueError("Accès refusé.")

        role = self.roles.get_by_id(role_id)
        if not role:
            raise ValueError("Rôle introuvable.")
        return self.role_serializer.serialize(role)

    def get_role_by_name(self, name: str) -> Dict[str, Any]:
        me = self._get_current_user()
        if not Permission.read_permission(me, "user"):
            raise ValueError("Accès refusé.")

        if not Permission.is_admin(me) and name == "admin":
            raise ValueError("Accès refusé.")

        role = self.roles.find_by_name(name)
        if not role:
            raise ValueError("Rôle introuvable.")
        return self.role_serializer.serialize(role)
