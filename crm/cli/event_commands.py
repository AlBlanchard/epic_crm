import click
from ..controllers.user_controller import UserController
from ..controllers.contract_controller import ContractController
from ..controllers.client_controller import ClientController
from ..controllers.event_controller import EventController
from ..views.contract_view import ContractView
from ..views.client_view import ClientView
from ..views.event_view import EventView
from ..database import SessionLocal
from ..auth.permission import Permission
from ..auth.permission_config import Crud
from ..errors.exceptions import UserCancelledInput
from decimal import Decimal


@click.command(name="create-event")
@click.option("--contractid", "contract_id", type=int, help="ID du contrat à associer")
@click.pass_context
def create_event_cmd(ctx: click.Context, contract_id: int) -> None:
    view: EventView = (
        ctx.obj.get("event_view")
        if ctx and ctx.obj and "event_view" in ctx.obj
        else EventView()
    )

    contract_view: ContractView = (
        ctx.obj.get("contract_view")
        if ctx and ctx.obj and "contract_view" in ctx.obj
        else ContractView()
    )

    ctrl: EventController = ctx.obj.get("event_controller") or EventController(
        session=SessionLocal()
    )

    contract_ctrl: ContractController = ctx.obj.get(
        "contract_controller"
    ) or ContractController(session=SessionLocal())

    user_ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    me = user_ctrl._get_current_user()
    if not Permission.create_permission(me, "event"):
        raise PermissionError("Accès refusé.")

    # Sélection du contrat à qui sera attaché l'événement
    if not contract_id:
        # Peut il tout update ? On liste tous les contrats
        if Permission.update_permission(me, "contract"):
            rows = contract_ctrl.list_signed_contracts()
        # Peut il seulement update ses propres contrats ? On liste ses propres contrats
        elif Permission.update_own_permission(me, "contract"):
            rows = contract_ctrl.list_signed_contracts(sales_contact_id=me.id)
        else:
            raise PermissionError("Accès refusé.")

        # Liste pour selectionner le contrat à modifier
        selected_id = contract_view.list_contracts(rows, selector=True)
        if selected_id is None:
            return
        contract_id = selected_id

    result = view.create_event_flow(contract_id)
    if result is None:
        return

    data = result

    try:
        ctrl.create_event(data)
        view.app_state.set_success_message("L'événement a été créé avec succès.")
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))
