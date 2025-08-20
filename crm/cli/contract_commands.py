import click
from ..controllers.user_controller import UserController
from ..controllers.contract_controller import ContractController
from ..controllers.client_controller import ClientController
from ..views.contract_view import ContractView
from ..views.client_view import ClientView
from ..database import SessionLocal
from ..auth.permission import Permission
from ..auth.permission_config import Crud


@click.command(name="create-contract")
@click.option("--clientid", "client_id", type=int, help="ID du client à modifier")
@click.pass_context
def create_contract_cmd(ctx: click.Context, client_id: int) -> None:
    view: ContractView = (
        ctx.obj.get("contract_view")
        if ctx and ctx.obj and "contract_view" in ctx.obj
        else ContractView()
    )
    ctrl: ContractController = ctx.obj.get("contract_controller") or ContractController(
        session=SessionLocal()
    )

    user_ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    client_ctrl: ClientController = ctx.obj.get(
        "client_controller"
    ) or ClientController(session=SessionLocal())

    client_view: ClientView = ctx.obj.get("client_view") or ClientView()

    me = user_ctrl._get_current_user()

    if not Permission.create_permission(me, "contract"):
        raise PermissionError("Accès refusé.")

    # Sélection du client à qui sera attaché le contrat
    if not client_id:
        rows = client_ctrl.list_clients()
        # Liste pour selectionner le client à modifier
        id_list = [r["sales_contact_id"] for r in rows]
        user_name_dict = user_ctrl.get_users_name_from_id_list(id_list)
        selected_id = client_view.list_clients(rows, user_name_dict, selector=True)
        if selected_id is None:
            return
        client_id = selected_id

    result = view.create_contract_flow(client_id)
    if result is None:
        return

    data = result

    try:
        ctrl.create_contract(data)
        view.app_state.set_success_message("Le contrat a été créé avec succès.")
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))
