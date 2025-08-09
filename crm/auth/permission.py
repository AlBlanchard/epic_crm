from typing import Optional


class Permission:
    """
    Classe centralisée pour gérer les règles d'accès aux entités
    selon les rôles de l'utilisateur et le principe du moindre privilège.
    """

    @staticmethod
    def is_admin(user) -> bool:
        return any(role.name == "admin" for role in user.roles)

    @staticmethod
    def is_owner(user, owner_id: Optional[int]) -> bool:
        return user.id == owner_id if owner_id is not None else False

    @staticmethod
    def has_permission(user, owner_id) -> bool:
        if Permission.is_owner(user, owner_id):
            return True
        if Permission.is_admin(user):
            return True
        return False
