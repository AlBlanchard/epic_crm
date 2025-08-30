from typing import Optional

from .permission_config import Crud, ROLE_RULES


class Permission:
    """
    Classe centralisée pour gérer les règles d'accès aux entités
    selon les rôles de l'utilisateur et le principe du moindre privilège.
    """

    @staticmethod
    def role_permissions(user) -> dict[str, set[Crud]]:
        """Retourne les permissions de chaque rôle de l'utilisateur."""
        permissions = {}
        for role in Permission.user_roles_list(user):
            permissions[role] = ROLE_RULES.get(role, {})
        return permissions

    @staticmethod
    def user_roles_list(user) -> list[str]:
        if not user or not hasattr(user, "roles"):
            raise ValueError("L'utilisateur doit avoir des rôles définis.")
        return [
            role.name.lower() for role in user.roles
        ]  # <-- normalisation en minuscules

    @staticmethod
    def role_allows(user, resource: str, op: Crud) -> bool:
        """Vérifie si le rôle de l'utilisateur permet l'opération sur la ressource."""
        user_roles_list = Permission.user_roles_list(user)
        for role in user_roles_list:
            # Va chercher les règles pour le rôle
            rules = ROLE_RULES.get(role, {})
            # Dans le cas d'un "*" (admin par exemple), on autorise directement
            if op in rules.get("*", set()):
                return True
            # Autorise si l'opération est bien dans la liste des règles pour la ressource
            if op in rules.get(resource, set()):
                return True
        return False

    @staticmethod
    def is_admin(user) -> bool:
        return any(role.name == "admin" for role in user.roles)

    @staticmethod
    def has_permission(
        user,
        *,
        resource: str,
        op: Crud,
        owner_id: int | None = None,
        target_id: int | None = None,
        own_only: bool = False
    ) -> bool:
        user_id = getattr(user, "id", None)
        # Admin
        if Permission.role_allows(user, "*", op):
            return True

        # Me
        if (
            resource == "user"
            and user_id is not None
            and target_id is not None
            and target_id == user_id
        ):
            return True

        # Règles de rôles sans notion d'owner
        if not own_only:
            if Permission.role_allows(user, resource, op):
                return True

        # Vérifie s'il peut en tant qu'owner
        if owner_id is not None:
            if user.id == owner_id:
                if op == Crud.READ:
                    return Permission.role_allows(user, resource, Crud.READ_OWN)
                if op == Crud.UPDATE:
                    return Permission.role_allows(user, resource, Crud.UPDATE_OWN)
                if op == Crud.DELETE:
                    return Permission.role_allows(user, resource, Crud.DELETE_OWN)
        return False

    @staticmethod
    def read_permission(
        user, resource: str, target_id: int | None = None, owner_id: int | None = None
    ) -> bool:
        return Permission.has_permission(
            user,
            resource=resource,
            op=Crud.READ,
            target_id=target_id,
            owner_id=owner_id,
        )

    @staticmethod
    def create_permission(
        user, resource: str, target_id: int | None = None, owner_id: int | None = None
    ) -> bool:
        return Permission.has_permission(
            user,
            resource=resource,
            op=Crud.CREATE,
            target_id=target_id,
            owner_id=owner_id,
        )

    @staticmethod
    def update_permission(
        user,
        resource: str,
        target_id: int | None = None,
        owner_id: int | None = None,
        own_only: bool = False,
    ) -> bool:
        return Permission.has_permission(
            user,
            resource=resource,
            op=Crud.UPDATE,
            target_id=target_id,
            owner_id=owner_id,
            own_only=own_only,
        )

    @staticmethod
    def delete_permission(
        user, resource: str, target_id: int | None = None, owner_id: int | None = None
    ) -> bool:
        return Permission.has_permission(
            user,
            resource=resource,
            op=Crud.DELETE,
            target_id=target_id,
            owner_id=owner_id,
        )

    @staticmethod
    def update_own_permission(user, resource: str) -> bool:
        return Permission.has_permission(
            user,
            resource=resource,
            op=Crud.UPDATE_OWN,
        )

    @staticmethod
    def delete_own_permission(user, resource: str) -> bool:
        return Permission.has_permission(
            user,
            resource=resource,
            op=Crud.DELETE_OWN,
        )
