# crm/controllers/user_controller.py
from typing import Dict, Any, Optional, List
from .base import AbstractController
from ..auth.auth import Authentication
from ..auth.permission import Permission
from ..crud.user_crud import UserCRUD
from ..crud.role_crud import RoleCRUD
from ..serializers.user_serializer import UserSerializer
from ..models.user import User


class UserController(AbstractController):
    """Logique métier pour Users : auth, permissions, orchestration CRUD."""

    def _setup_services(self) -> None:
        self.users = UserCRUD(self.session)
        self.roles = RoleCRUD(self.session)
        # sérialiseur par défaut : champs publics + rôles
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
    def list_users(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        fields: Optional[List[str]] = None,
        include_roles: bool = True,
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        self._ensure_admin(me)
        rows = self.users.get_all(filters=filters, order_by=order_by)
        # sérialiseur custom si besoin de restreindre les champs/roles
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
        ser = (
            self.serializer
            if (fields is None and include_roles)
            else UserSerializer(fields=fields, include_roles=include_roles)
        )
        return ser.serialize(me)

    # ---------- Create ----------
    def create_user(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attendu (validé en amont) :
        - username, email, employee_number, password
        - role_names: List[str] (optionnel, admin only)
        """
        me = self._get_current_user()
        self._ensure_admin(me)

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
        self._ensure_admin(me)
        if me.id == user_id:
            raise PermissionError("Vous ne pouvez pas supprimer votre propre compte.")

        ok = self.users.delete_user(user_id)
        if not ok:
            raise ValueError("Utilisateur introuvable.")

    # ---------- Roles ----------
    def add_role(self, user_id: int, role_name: str) -> None:
        me = self._get_current_user()
        self._ensure_admin(me)

        role = self.roles.find_by_name(role_name)
        if not role:
            raise ValueError(f"Rôle '{role_name}' introuvable.")
        self.users.add_role_to_user(user_id, role.id)

    def remove_role(self, user_id: int, role_name: str) -> None:
        me = self._get_current_user()
        self._ensure_admin(me)

        role = self.roles.find_by_name(role_name)
        if not role:
            raise ValueError(f"Rôle '{role_name}' introuvable.")
        ok = self.users.remove_role_from_user(user_id, role.id)
        if not ok:
            raise ValueError("Rôle non associé à l'utilisateur.")

    def replace_roles(self, user_id: int, role_names: List[str]) -> None:
        me = self._get_current_user()
        self._ensure_admin(me)

        roles = [r for r in (self.roles.find_by_name(n) for n in role_names) if r]
        if len(roles) != len(role_names):
            missing = set(role_names) - {r.name for r in roles}
            raise ValueError(f"Rôles introuvables: {', '.join(sorted(missing))}")
        self.users.replace_user_roles(user_id, [r.id for r in roles])
