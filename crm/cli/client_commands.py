import click
from ..controllers.client_controller import ClientController
from ..controllers.user_controller import UserController
from ..views.client_view import ClientView
from ..database import SessionLocal
from ..auth.permission import Permission


@click.command(name="create-client")
@click.pass_context
def create_client_cmd(ctx: click.Context) -> None:
    # On réutilise la vue attachée au contexte si dispo, sinon on en crée une
    view: ClientView = (
        ctx.obj.get("client_view")
        if ctx and ctx.obj and "client_view" in ctx.obj
        else ClientView()
    )
    ctrl: ClientController = ctx.obj.get("user_controller") or ClientController(
        session=SessionLocal()
    )

    user_ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    # Il y a une vérif dans le ctrl mais on la refait ici sinon ça lance les prompts
    me = user_ctrl._get_current_user()
    if not Permission.create_permission(me, "client"):
        raise PermissionError("Accès refusé.")

    result = view.create_client_flow(sales_contact_id=me.id)
    if result is None:
        return

    data = result

    try:
        ctrl.create_client(data)
        view.app_state.set_success_message("Le client a été créé avec succès.")
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="list-clients")
@click.pass_context
def list_clients_cmd(ctx: click.Context) -> None:
    view: ClientView = (
        ctx.obj.get("client_view")
        if ctx and ctx.obj and "client_view" in ctx.obj
        else ClientView()
    )

    ctrl: ClientController = ctx.obj.get("client_controller") or ClientController(
        session=SessionLocal()
    )

    user_ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    rows = ctrl.list_clients()
    id_list = [r["id"] for r in rows]
    user_name_tuples = user_ctrl.get_users_name_from_id_list(id_list)
    view.list_clients(rows, user_name_tuples, selector=False)
