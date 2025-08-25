from typing import Dict, Any, Optional, List
from .base import AbstractController
from ..crud.role_crud import RoleCRUD
from ..crud.user_crud import UserCRUD
from ..serializers.user_serializer import UserSerializer
from ..serializers.role_serializer import RoleSerializer


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
        self._ensure_admin(me)
        rows = self.roles.get_all(filters=filters, order_by=order_by)
        return self.role_serializer.serialize_list(rows)

    def get_role(self, role_id: int) -> Dict[str, Any]:
        me = self._get_current_user()
        self._ensure_admin(me)
        role = self.roles.get_by_id(role_id)
        if not role:
            raise ValueError("Rôle introuvable.")
        return self.role_serializer.serialize(role)

    def get_role_by_name(self, name: str) -> Dict[str, Any]:
        me = self._get_current_user()
        self._ensure_admin(me)
        role = self.roles.find_by_name(name)
        if not role:
            raise ValueError("Rôle introuvable.")
        return self.role_serializer.serialize(role)
