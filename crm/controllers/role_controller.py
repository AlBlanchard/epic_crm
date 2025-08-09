from typing import Dict, Any, Optional, List
from .base import AbstractController
from ..auth.auth import Authentication
from ..auth.permission import Permission
from ..crud.role_crud import RoleCRUD
from ..crud.user_crud import UserCRUD
from ..serializers.user_serializer import UserSerializer
from ..serializers.role_serializer import RoleSerializer
from ..models.user import User


class RoleController(AbstractController):
    """Logique métier pour Roles : admin-only pour la gestion."""

    def _setup_services(self) -> None:
        self.roles = RoleCRUD(self.session)
        self.users = UserCRUD(self.session)
        self.role_serializer = RoleSerializer()
        self.user_serializer = UserSerializer()

    # ---------- Helpers ----------
    def _get_current_user(self) -> User:
        token = Authentication.load_token()
        if not token:
            raise PermissionError("Non authentifié.")
        payload = Authentication.verify_token(token)
        me = self.users.get_by_id(int(payload["sub"]))
        if not me:
            raise PermissionError("Utilisateur courant introuvable.")
        return me

    def _ensure_admin(self, me: User) -> None:
        if not Permission.is_admin(me):
            raise PermissionError("Accès refusé : administrateur requis.")

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

    # ---------- Create / Update / Delete ----------
    def create_role(self, name: str) -> Dict[str, Any]:
        me = self._get_current_user()
        self._ensure_admin(me)
        role = self.roles.create_role({"name": name})
        return self.role_serializer.serialize(role)

    def update_role(self, role_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        me = self._get_current_user()
        self._ensure_admin(me)
        role = self.roles.update_role(role_id, data)
        if not role:
            raise ValueError("Rôle introuvable.")
        return self.role_serializer.serialize(role)

    def delete_role(self, role_id: int) -> None:
        me = self._get_current_user()
        self._ensure_admin(me)
        # Empêche par défaut de supprimer un rôle encore assigné
        ok = self.roles.delete_role(role_id)
        if not ok:
            raise ValueError("Rôle introuvable.")

    # ---------- Users <-> Role ----------
    def users_with_role(self, role_name: str) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        self._ensure_admin(me)
        users = self.roles.get_users_with_role_by_name(role_name)
        return self.user_serializer.serialize_list(users)

    def add_user_to_role(self, user_id: int, role_name: str) -> None:
        me = self._get_current_user()
        self._ensure_admin(me)
        role = self.roles.find_by_name(role_name)
        if not role:
            raise ValueError(f"Rôle '{role_name}' introuvable.")
        self.roles.add_user_to_role(role.id, user_id)

    def remove_user_from_role(self, user_id: int, role_name: str) -> None:
        me = self._get_current_user()
        self._ensure_admin(me)
        role = self.roles.find_by_name(role_name)
        if not role:
            raise ValueError(f"Rôle '{role_name}' introuvable.")
        ok = self.roles.remove_user_from_role(role.id, user_id)
        if not ok:
            raise ValueError("Cet utilisateur n'avait pas ce rôle.")

    def replace_role_users(self, role_name: str, user_ids: List[int]) -> None:
        me = self._get_current_user()
        self._ensure_admin(me)
        role = self.roles.find_by_name(role_name)
        if not role:
            raise ValueError(f"Rôle '{role_name}' introuvable.")
        self.roles.replace_role_users(role.id, user_ids)

    # ---------- Utilities ----------
    def stats(self, role_id: int) -> Dict[str, Any]:
        me = self._get_current_user()
        self._ensure_admin(me)
        return self.roles.get_role_stats(role_id)
