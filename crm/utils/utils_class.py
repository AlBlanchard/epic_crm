from ..controllers.user_controller import UserController
from ..controllers.client_controller import ClientController
from ..controllers.contract_controller import ContractController
from ..controllers.event_controller import EventController

ENTITY_TO_CONTROLLER = {
    "users": UserController,
    "clients": ClientController,
    "contracts": ContractController,
    "events": EventController,
}

class Utils:
    def __init__(self):
        self.user_ctrl = UserController()

    def get_all_users_by_role(
        self,
        role_name: str,
        *,
        order_by: str | None = None,
        fields: list[str] | None = None,
        include_roles: bool = True,
    ) -> list[dict]:
        return self.user_ctrl.get_all_users_by_role(
            role_name,
            order_by=order_by,
            fields=fields,
            include_roles=include_roles,
        )