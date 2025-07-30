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
    def has_role(user, allowed_roles: list[str]) -> bool:
        return any(role.name in allowed_roles for role in user.roles)

    # LECTURE CLIENTS
    @staticmethod
    def can_view_clients(user, target_user_id: Optional[int] = None) -> bool:
        if target_user_id is None:
            return Permission.has_role(user, ["sales"])
        return Permission.is_admin(user)

    # LECTURE CONTRATS
    @staticmethod
    def can_view_contracts(user, target_user_id: Optional[int] = None) -> bool:
        if target_user_id is None:
            return Permission.has_role(user, ["sales"])
        return Permission.is_admin(user)

    # LECTURE EVENEMENTS
    @staticmethod
    def can_view_events(user, target_user_id: Optional[int] = None) -> bool:
        if target_user_id is None:
            return Permission.has_role(user, ["support"])
        return Permission.is_admin(user)

    # CREATION DE DONNEES
    @staticmethod
    def can_create_client(user) -> bool:
        return Permission.has_role(user, ["sales"])

    @staticmethod
    def can_create_contract(user) -> bool:
        return Permission.has_role(user, ["sales"])

    @staticmethod
    def can_create_event(user) -> bool:
        return Permission.has_role(user, ["support"])

    # MODIFICATION
    @staticmethod
    def can_edit_client(user, client_owner_id: int) -> bool:
        return Permission.is_admin(user) or user.id == client_owner_id

    @staticmethod
    def can_edit_contract(user, contract_owner_id: int) -> bool:
        return Permission.is_admin(user) or user.id == contract_owner_id

    @staticmethod
    def can_edit_event(user, event_owner_id: int) -> bool:
        return Permission.is_admin(user) or user.id == event_owner_id
