import click
from ..controllers.user_controller import UserController
from ..controllers.contract_controller import ContractController
from ..controllers.event_controller import EventController
from ..views.contract_view import ContractView
from ..views.user_view import UserView
from ..views.event_view import EventView
from ..database import SessionLocal
from ..auth.permission import Permission
from .filter_commands import filter_cmd


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
        selected_id = contract_view.list_all(rows, selector=True)
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


@click.command(name="list-events")
@click.pass_context
def list_events_cmd(ctx: click.Context) -> None:
    view: EventView = (
        ctx.obj.get("event_view")
        if ctx and ctx.obj and "event_view" in ctx.obj
        else EventView()
    )

    ctrl: EventController = ctx.obj.get("event_controller") or EventController(
        session=SessionLocal()
    )

    try:
        rows = ctrl.list_all()
        want_filter = view.list_all(rows, has_filter=True)

        if want_filter:
            ctx.invoke(filter_cmd, entity="events")
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="update-event")
@click.option("--eventid", "event_id", type=int, help="ID de l'événement à modifier")
@click.pass_context
def update_event_cmd(ctx: click.Context, event_id: int) -> None:
    view: EventView = (
        ctx.obj.get("event_view")
        if ctx and ctx.obj and "event_view" in ctx.obj
        else EventView()
    )

    ctrl: EventController = ctx.obj.get("event_controller") or EventController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if not Permission.update_permission(me, "event", event_id):
        raise PermissionError("Accès refusé.")

    if not event_id:
        if Permission.update_permission(me, "event"):
            rows = ctrl.list_all()
        elif Permission.update_own_permission(me, "event"):
            rows = ctrl.list_my_events()
        else:
            raise PermissionError("Accès refusé.")

        selected_id = view.list_all(rows, selector=True)
        if selected_id is None:
            return
        event_id = selected_id

    event = ctrl.get_event(event_id)
    new_data = view.update_event_flow(event)

    if not new_data:
        return

    try:
        ctrl.update_event(event_id, new_data)
        view.app_state.set_success_message("L'événement a été mis à jour avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command(name="add-event-note")
@click.option(
    "--eventid", "event_id", type=int, help="ID de l'événement auquel ajouter une note"
)
@click.pass_context
def add_event_note_cmd(ctx: click.Context, event_id: int) -> None:
    view: EventView = (
        ctx.obj.get("event_view")
        if ctx and ctx.obj and "event_view" in ctx.obj
        else EventView()
    )

    ctrl: EventController = ctx.obj.get("event_controller") or EventController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if not Permission.update_permission(me, "event", event_id):
        raise PermissionError("Accès refusé.")

    if not event_id:
        if Permission.update_permission(me, "event"):
            rows = ctrl.list_all()
        elif Permission.update_own_permission(me, "event"):
            rows = ctrl.list_my_events()
        else:
            raise PermissionError("Accès refusé.")

        selected_id = view.list_all(rows, selector=True)
        if selected_id is None:
            return
        event_id = selected_id

    note = view.add_event_note_flow()

    try:
        ctrl.create_note(event_id, note)
        view.app_state.set_success_message("La note a été ajoutée avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command(name="delete-note")
@click.option(
    "--eventid",
    "event_id",
    type=int,
    help="ID de l'événement auquel supprimer une note",
)
@click.pass_context
def delete_note_cmd(ctx: click.Context, event_id: int) -> None:
    view: EventView = (
        ctx.obj.get("event_view")
        if ctx and ctx.obj and "event_view" in ctx.obj
        else EventView()
    )

    ctrl: EventController = ctx.obj.get("event_controller") or EventController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if not Permission.update_permission(me, "event", event_id):
        raise PermissionError("Accès refusé.")

    if not event_id:
        if Permission.update_permission(me, "event"):
            rows = ctrl.list_all()
        elif Permission.update_own_permission(me, "event"):
            rows = ctrl.list_my_events()
        else:
            raise PermissionError("Accès refusé.")

        selected_id = view.list_all(rows, selector=True)
        if selected_id is None:
            return
        event_id = selected_id

    notes_list = ctrl.list_event_notes(event_id)
    selected_note_id = view.list_notes(notes_list, selector=True)
    if selected_note_id is None:
        return

    try:
        ctrl.delete_note(event_id, selected_note_id)
        view.app_state.set_success_message("La note a été supprimée avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command("update-support")
@click.option("--eventid", "event_id", type=int, help="ID de l'événement à modifier")
@click.option("--supportid", "new_support_id", type=int, help="ID du nouveau support")
@click.pass_context
def update_support_cmd(
    ctx: click.Context, event_id: int | None = None, new_support_id: int | None = None
) -> None:
    view: EventView = (
        ctx.obj.get("event_view")
        if ctx and ctx.obj and "event_view" in ctx.obj
        else EventView()
    )

    user_view: UserView = (
        ctx.obj.get("user_view")
        if ctx and ctx.obj and "user_view" in ctx.obj
        else UserView()
    )

    ctrl: EventController = ctx.obj.get("event_controller") or EventController(
        session=SessionLocal()
    )

    user_ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if not Permission.update_permission(me, "event", event_id):
        raise PermissionError("Accès refusé.")

    if not event_id:
        if Permission.update_permission(me, "event"):
            rows = ctrl.list_all()
        elif Permission.update_own_permission(me, "event"):
            rows = ctrl.list_my_events()
        else:
            raise PermissionError("Accès refusé.")

        selected_id = view.list_all(rows, selector=True)
        if selected_id is None:
            return
        event_id = selected_id

    if not new_support_id:
        if Permission.read_permission(me, "user"):
            rows = user_ctrl.get_all_users_by_role("support")
        else:
            raise PermissionError("Accès refusé.")

        selected_id = user_view.list_users(rows, selector=True)
        if selected_id is None:
            return
        new_support_id = selected_id

    payload = {}
    if new_support_id:
        payload["support_contact_id"] = new_support_id

    try:
        ctrl.update_event(event_id, payload)
        view.app_state.set_success_message("L'événement a été mis à jour avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command(name="delete-event")
@click.option("--eventid", "event_id", type=int, help="ID de l'événement à supprimer")
@click.pass_context
def delete_event_cmd(ctx: click.Context, event_id: int | None = None) -> None:
    view: EventView = (
        ctx.obj.get("event_view")
        if ctx and ctx.obj and "event_view" in ctx.obj
        else EventView()
    )

    ctrl: EventController = ctx.obj.get("event_controller") or EventController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if not Permission.delete_permission(me, "event", event_id):
        raise PermissionError("Accès refusé.")

    if not event_id:
        if Permission.delete_permission(me, "event"):
            rows = ctrl.list_all()
        elif Permission.delete_own_permission(me, "event"):
            rows = ctrl.list_my_events()
        else:
            raise PermissionError("Accès refusé.")

        selected_id = view.list_all(rows, selector=True)
        if selected_id is None:
            return
        event_id = selected_id

    try:
        ctrl.delete_event(event_id)
        view.app_state.set_success_message("L'événement a été supprimé avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))
