import click
from ..controllers.client_controller import ClientController
from ..controllers.user_controller import UserController
from ..views.client_view import ClientView
from ..views.user_view import UserView
from ..database import SessionLocal
from ..auth.permission import Permission
from ..auth.permission_config import Crud


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
    try:
        # Il y a une vérif dans le ctrl mais on la refait ici sinon ça lance les prompts
        me = user_ctrl._get_current_user()
        if not Permission.create_permission(me, "client"):
            raise PermissionError("Accès refusé.")

        result = view.create_client_flow(sales_contact_id=me.id)
        if result is None:
            return

        ctrl.create_client(result)
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

    rows = ctrl.list_clients()
    view.list_clients(rows)


@click.command(name="update-client")
@click.option("--id", "client_id", type=int, help="ID du client à modifier")
@click.pass_context
def update_client_cmd(ctx: click.Context, client_id: int) -> None:
    view: ClientView = (
        ctx.obj.get("client_view")
        if ctx and ctx.obj and "client_view" in ctx.obj
        else ClientView()
    )

    ctrl: ClientController = ctx.obj.get("client_controller") or ClientController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()

    # Vérification des permissions afin de lister les clients qui peuvent être modifiés
    if not client_id:
        # Peut il tout update ? On liste tous les clients
        if Permission.update_permission(me, "client"):
            rows = ctrl.list_clients()
        # Peut il seulement update ses propres clients ? On liste ses propres clients
        elif Permission.update_own_permission(me, "client"):
            rows = ctrl.list_my_clients()
        else:
            raise PermissionError("Accès refusé.")

        # Liste pour selectionner le client à modifier
        selected_id = view.list_clients(rows, selector=True)
        if selected_id is None:
            return
        client_id = selected_id

    # Vérifie encore les permissions dans le cas où l'id est directement fourni
    # Ou même par source de vérité
    owner = ctrl.get_owner(client_id)
    if not Permission.update_permission(me, "client", owner_id=owner.id):
        raise PermissionError(f"Accès refusé.")

    client_dict = ctrl.get_client(client_id)
    result = view.update_client_flow(client_dict)
    if result is None:
        return

    client_id, payload = result

    try:
        ctrl.update_client(client_id, payload)
        view.app_state.set_success_message("Le client a été mis à jour avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command(name="update-sales-contact")
@click.option("--id", "client_id", type=int, help="ID du client à modifier")
@click.option(
    "--salesid", "new_sales_id", type=int, help="ID du nouveau contact commercial"
)
@click.pass_context
def update_sales_contact_cmd(
    ctx: click.Context, client_id: int, new_sales_id: int
) -> None:
    view: ClientView = (
        ctx.obj.get("client_view")
        if ctx and ctx.obj and "client_view" in ctx.obj
        else ClientView()
    )

    user_view: UserView = (
        ctx.obj.get("user_view")
        if ctx and ctx.obj and "user_view" in ctx.obj
        else UserView()
    )

    ctrl: ClientController = ctx.obj.get("client_controller") or ClientController(
        session=SessionLocal()
    )

    user_ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()

    if not Permission.is_admin(me):
        raise PermissionError("Accès refusé.")

    if not client_id:
        rows = ctrl.list_clients()
        selected_id = view.list_clients(rows, selector=True)
        if selected_id is None:
            return
        client_id = selected_id

    if not new_sales_id:
        sales_list = user_ctrl.get_all_users_by_role("sales")
        sales_list = sales_list + user_ctrl.get_all_users_by_role("admin")
        selected_id = user_view.list_users(
            sales_list,
            selector=True,
            prompt="[yellow]Sélectionnez un nouveau contact commercial...[/yellow]",
        )
        if selected_id is None:
            return
        new_sales_id = selected_id

    payload = {"sales_contact_id": new_sales_id}

    try:
        ctrl.update_client(client_id, payload)
        view.app_state.set_success_message(
            "Le contact commercial a été mis à jour avec succès."
        )
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command(name="delete-client")
@click.option("--id", "client_id", type=int, help="ID du client à supprimer")
@click.pass_context
def delete_client_cmd(ctx: click.Context, client_id: int) -> None:
    view: ClientView = (
        ctx.obj.get("client_view")
        if ctx and ctx.obj and "client_view" in ctx.obj
        else ClientView()
    )

    ctrl: ClientController = ctx.obj.get("client_controller") or ClientController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()

    if not Permission.is_admin(me):
        raise PermissionError("Accès refusé.")

    if not client_id:
        rows = ctrl.list_clients()
        selected_id = view.list_clients(rows, selector=True)
        if selected_id is None:
            return
        client_id = selected_id

    try:
        ctrl.delete_client(client_id)
        view.app_state.set_success_message("Le client a été supprimé avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))
