# crm/controllers/user_controller.py
from typing import Dict, Any, Optional, List
from .base import AbstractController
from ..auth.auth import Authentication
from ..auth.permission import Permission
from ..crud.user_crud import UserCRUD
from ..crud.role_crud import RoleCRUD
from ..serializers.user_serializer import UserSerializer
from ..models.user import User
from ..utils.app_state import AppState


class UserController(AbstractController):
    """Logique métier pour Users : auth, permissions, orchestration CRUD."""

    def _setup_services(self) -> None:
        self.users = UserCRUD(self.session)
        self.roles = RoleCRUD(self.session)
        self.serializer = UserSerializer()

    # ---------- Helpers ----------
    def _get_current_user(self) -> User:
        token = Authentication.load_token()
        if not token:
            raise PermissionError("Non authentifié.")
        payload = Authentication.verify_token(token)
        user_id = int(payload["sub"])
        user = self.users.get_by_id(user_id)
        if not user:
            raise PermissionError("Utilisateur courant introuvable.")
        return user

    def _ensure_admin(self, me: User) -> None:
        if not Permission.is_admin(me):
            raise PermissionError("Accès refusé : administrateur requis.")

    def _serialize_many(self, rows: List[User]) -> List[Dict[str, Any]]:
        return self.serializer.serialize_list(rows)

    # ---------- Read ----------
    def get_all_users(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        fields: Optional[List[str]] = None,
        include_roles: bool = True,
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()

        if not Permission.read_permission(me, "user"):
            raise PermissionError("Accès refusé.")

        rows = self.users.get_all(filters=filters, order_by=order_by)
        ser = (
            self.serializer
            if (fields is None and include_roles)
            else UserSerializer(fields=fields, include_roles=include_roles)
        )
        return ser.serialize_list(rows)

    def get_user(
        self,
        user_id: int,
        *,
        fields: Optional[List[str]] = None,
        include_roles: bool = True,
    ) -> Dict[str, Any]:
        me = self._get_current_user()
        target = self.users.get_by_id(user_id)

        if not Permission.read_permission(me, "user", target_id=user_id):
            raise PermissionError("Accès refusé.")

        if not target:
            raise ValueError("Utilisateur introuvable.")

        if not (Permission.is_admin(me) or me.id == target.id):
            raise PermissionError("Accès refusé.")

        ser = (
            self.serializer
            if (fields is None and include_roles)
            else UserSerializer(fields=fields, include_roles=include_roles)
        )
        return ser.serialize(target)

    def me(
        self,
        *,
        fields: Optional[List[str]] = None,
        include_roles: bool = True,
    ) -> Dict[str, Any]:
        me = self._get_current_user()

        if not Permission.read_permission(me, "user", target_id=me.id):
            raise PermissionError("Accès refusé.")

        ser = (
            self.serializer
            if (fields is None and include_roles)
            else UserSerializer(fields=fields, include_roles=include_roles)
        )
        return ser.serialize(me)

    def get_user_name(self, user_id: int) -> str:
        user = self.users.get_by_id(user_id)
        me = self._get_current_user()

        if not Permission.read_permission(me, "user", target_id=user_id):
            raise PermissionError("Accès refusé.")

        if not user:
            raise ValueError("Utilisateur introuvable.")
        return user.username

    # ---------- Create ----------
    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attendu (validé en amont) :
        - username, email, employee_number, password
        - role_names: List[str] (optionnel, admin only)
        """
        me = self._get_current_user()

        if not Permission.create_permission(me, "user"):
            raise PermissionError("Accès refusé.")

        user = self.users.create_user(data)  # set_password géré dans le CRUD
        return self.serializer.serialize(user)

    # ---------- Update ----------
    def update_user(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        - Un user peut modifier son propre profil (+ password)
        - Seul un admin peut modifier n'importe quel user
        - Seul un admin peut modifier les rôles via role_names
        """
        me = self._get_current_user()
        target = self.users.get_by_id(user_id)

        if not Permission.update_permission(me, "user", target_id=user_id):
            raise PermissionError("Accès refusé.")

        if not target:
            raise ValueError("Utilisateur introuvable.")

        is_self = me.id == target.id
        is_admin = Permission.is_admin(me)

        if not is_admin and "role_names" in data:
            data = {k: v for k, v in data.items() if k != "role_names"}

        if not (is_admin or is_self):
            raise PermissionError("Accès refusé.")

        updated = self.users.update_user(user_id, data)
        if updated is None:
            raise ValueError("Mise à jour impossible.")
        return self.serializer.serialize(updated)

    def change_password(self, user_id: int, new_password: str) -> None:
        me = self._get_current_user()
        if not (Permission.is_admin(me) or me.id == user_id):
            raise PermissionError("Accès refusé.")

        ok = self.users.update_password(user_id, new_password)
        if not ok:
            raise ValueError("Utilisateur introuvable ou échec de mise à jour.")

    # ---------- Delete ----------
    def delete_user(self, user_id: int) -> None:
        me = self._get_current_user()

        if not Permission.delete_permission(me, "user", target_id=user_id):
            raise PermissionError("Accès refusé.")

        ok = self.users.delete_user(user_id)
        if not ok:
            raise ValueError("Utilisateur introuvable.")

    # ---------- Roles ----------
    def add_role(
        self, user_id: int, role_id: int, create_new_user: bool = False
    ) -> None:
        me = self._get_current_user()

        if not create_new_user:
            if not Permission.create_permission(me, "user_role"):
                raise PermissionError("Accès refusé.")

        role = self.roles.get_by_id(role_id)
        if not role:
            raise ValueError(f"Rôle id : '{role_id}' introuvable.")

        if self.has_role(user_id, role.id):
            raise ValueError(f"L'utilisateur a déjà le rôle : {role.name}")

        self.users.add_role_to_user(user_id, role.id)

    def remove_role(self, user_id: int, role_id: int) -> None:
        me = self._get_current_user()

        if not Permission.delete_permission(me, "user_role"):
            raise PermissionError("Accès refusé.")

        role = self.roles.get_by_id(role_id)
        if not role:
            raise ValueError(f"Rôle id : '{role_id}' introuvable.")
        ok = self.users.remove_role_from_user(user_id, role.id)
        if not ok:
            raise ValueError("Rôle non associé à l'utilisateur.")

    def get_user_roles(self, user_id: int) -> List[str]:
        me = self._get_current_user()
        user = self.users.get_by_id(user_id)

        if not Permission.read_permission(me, "user", target_id=user_id):
            raise PermissionError("Accès refusé.")

        if not user:
            raise ValueError("Utilisateur introuvable.")
        return [r.name for r in user.roles]

    def has_role(self, user_id: int, role_id: int) -> bool:
        me = self._get_current_user()
        user = self.users.get_by_id(user_id)

        if not Permission.read_permission(me, "user", target_id=user_id):
            raise PermissionError("Accès refusé.")

        if not user:
            raise ValueError("Utilisateur introuvable.")
        return any(r.id == role_id for r in user.roles)
