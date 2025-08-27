import click
from ..controllers.user_controller import UserController
from ..controllers.role_controller import RoleController
from ..views.user_view import UserView
from ..views.menu_view import MenuView
from ..database import SessionLocal
from ..utils.validations import Validations
from ..errors.exceptions import UserCancelledInput
from ..auth.permission import Permission
from ..auth.auth import Authentication
from ..utils.audit_decorators import audit_command


@click.command(name="create-user")
@click.pass_context
@audit_command(category="user", action="create", event_level_on_success="info")
def create_user_cmd(ctx: click.Context) -> None:
    # On réutilise la vue attachée au contexte si dispo, sinon on en crée une
    view: UserView = (
        ctx.obj.get("user_view")
        if ctx and ctx.obj and "user_view" in ctx.obj
        else UserView()
    )
    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    # Il y a une vérif dans le ctrl mais on la refait ici car sinon ça lance les prompts
    me = ctrl._get_current_user()
    if not Permission.create_permission(me, "user"):
        raise PermissionError("Accès refusé.")

    employees_nbr = ctrl.get_all_employees_nbr()
    result = view.create_user_flow(employees_nbr)
    if result is None:
        return

    data, role_id = result

    try:
        new_user = ctrl.create_user(data)
        ctrl.add_role(new_user["id"], int(role_id), create_new_user=True)

        view.app_state.set_success_message("L'utilisateur a été créé avec succès.")
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="list-users")
@click.pass_context
def list_users_cmd(ctx: click.Context, user_id: int | None = None) -> None:
    # On réutilise la vue attachée au contexte si dispo, sinon on en crée une
    view: UserView = (
        ctx.obj.get("user_view")
        if ctx and ctx.obj and "user_view" in ctx.obj
        else UserView()
    )

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if not Permission.read_permission(me, "user"):
        if not Permission.read_permission(me, "user", owner_id=user_id):
            raise PermissionError("Accès refusé.")

    rows = ctrl.get_all_users(filters={"id": user_id} if user_id else None)
    view.list_users(rows, selector=False)


@click.command(name="update-user")
@click.option("--id", "user_id", type=int, help="ID de l'utilisateur à modifier")
@click.pass_context
@audit_command(category="user", action="update", event_level_on_success="info")
def update_user_cmd(ctx: click.Context, user_id: int | None) -> None:
    """Ouvre un menu de modification pour l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    user_view: UserView = ctx.obj.get("user_view") or UserView(console=console)
    menu_view: MenuView = ctx.obj.get("menu_view") or MenuView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = user_view.list_users(rows, selector=True)
        if not user_id:
            return

    target_user = ctrl.get_by_id(user_id)
    if Permission.is_admin(target_user) and user_id != me.id:
        raise PermissionError("Accès refusé.")

    username = ctrl.get_user_name(user_id)
    menu_view.modify_user_menu(user_id, username, ctx)


@click.command(name="update-user-infos")
@click.option("--id", "user_id", type=int, help="ID de l'utilisateur à modifier")
@click.pass_context
@audit_command(category="user", action="update", event_level_on_success="info")
def update_user_infos_cmd(ctx: click.Context, user_id: int | None) -> None:
    """Modifie les infos non sensibles de l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    # Permission pour ne pas lancer les prompts, verif dans le ctrl tout de même
    me = ctrl._get_current_user()
    if not Permission.update_permission(me, "user"):
        raise PermissionError("Accès refusé.")

    user_dict = ctrl.get_user(user_id)
    result = view.update_user_infos_flow(user_dict)

    if result is None:
        return

    uid, payload = result

    try:
        ctrl.update_user(uid, payload)
        if view.app_state:
            view.app_state.set_success_message(
                "L'utilisateur a été mis à jour avec succès."
            )
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="update-user-password")
@click.option(
    "--id",
    "user_id",
    type=int,
    help="ID de l'utilisateur dont le mot de passe doit être modifié",
)
@click.pass_context
@audit_command(
    category="user", action="update_password", event_level_on_success="warning"
)
def update_user_password_cmd(ctx: click.Context, user_id: int | None) -> None:
    """Modifie uniquement le mot de passe de l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if user_id:
        # Refuse si l'id n'est pas le miens
        if not Permission.update_permission(
            me, "user", owner_id=user_id, own_only=True
        ):
            # Si l'id n'est pas le miens, refuse si je ne suis pas admin
            if not Permission.is_admin(me):
                raise PermissionError("Accès refusé.")

    # Sélection de l'utilisateur si pas d'id transmis, ADMIN ONLY
    if not user_id:
        if not Permission.is_admin(me):
            raise PermissionError("Accès refusé.")

        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    # Dans le cas où l'admin modifie le mdp de quelqu'un d'autre, pas besoin de l'ancien mdp
    # Cependant s'il souhaite modifier son propre MDP, il doit fournir l'ancien mot de passe
    if me.id == int(user_id):
        view._clear_screen()
        view._print_back_choice()
        password = click.prompt("Ancien mot de passe", hide_input=True)
        try:
            if not Authentication.verify_password(password, me.password_hash):
                raise ValueError("Mot de passe incorrect.")
        except Exception as e:
            view.app_state.set_error_message(str(e))
            return

    UserView._clear_screen()
    new_pwd = view.update_user_password_flow()
    if new_pwd is None:
        return

    # revalidation côté ctrl, source de vérité
    try:
        _ = ctrl.get_user(int(user_id))
    except Exception as e:
        view.app_state.set_error_message(str(e))
        return

    try:
        ctrl.update_user(user_id, {"password": new_pwd})
        if view.app_state:
            view.app_state.set_success_message(
                "Le mot de passe de l'utilisateur a été mis à jour avec succès."
            )
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="delete-user")
@click.pass_context
@audit_command(category="user", action="delete", event_level_on_success="warning")
def delete_user_cmd(ctx: click.Context, user_id: int | None = None) -> None:
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    me = ctrl._get_current_user()
    if not Permission.delete_permission(me, "user"):
        raise PermissionError("Accès refusé.")

    try:
        user = ctrl.get_user(int(user_id))
    except Exception as e:
        view.app_state.set_error_message(str(e))
        return

    confirmed = view.delete_user_flow(user["username"])

    if not confirmed:
        raise UserCancelledInput("Suppression annulée par l'utilisateur.")

    try:
        ctrl.delete_user(user["id"])
        view.app_state.set_success_message("L'utilisateur a été supprimé avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command(name="add-user-role")
@click.option(
    "--id",
    "user_id",
    type=int,
    help="ID de l'utilisateur auquel ajouter un rôle",
)
@click.option(
    "--role",
    "role_id",
    type=int,
    help="ID du rôle à ajouter à l'utilisateur",
)
@click.pass_context
def add_user_role_cmd(
    ctx: click.Context, user_id: int | None, role_id: int | None
) -> None:
    """Ajoute un rôle à l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    role_ctrl: RoleController = ctx.obj.get("role_controller") or RoleController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    # Sélection du rôle si pas de rôle transmis
    if not role_id:
        roles = role_ctrl.list_roles()
        actual_roles = ctrl.get_user_roles(user_id)
        role_id = view.add_user_role_flow(actual_roles, roles)
        if not role_id:
            return

    # revalidation côté ctrl, source de vérité
    try:
        _ = ctrl.get_user(int(user_id))
        _ = role_ctrl.get_role(int(role_id))
    except Exception as e:
        view.app_state.set_error_message(str(e))
        return

    try:
        ctrl.add_role(user_id, role_id)
        if view.app_state:
            view.app_state.set_success_message(
                "Le rôle a été ajouté à l'utilisateur avec succès."
            )
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="remove-user-role")
@click.option(
    "--id",
    "user_id",
    type=int,
    help="ID de l'utilisateur dont on veut retirer un rôle",
)
@click.option(
    "--role",
    "role_name",
    type=str,
    help="Nom du rôle à retirer de l'utilisateur",
)
@click.pass_context
def remove_user_role_cmd(
    ctx: click.Context, user_id: int | None, role_name: str | None
) -> None:
    """Retire un rôle de l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    role_ctrl: RoleController = ctx.obj.get("role_controller") or RoleController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    # Sélection du rôle si pas de rôle transmis
    if not role_name:
        actual_roles = ctrl.get_user_roles(user_id)
        role_name = view.remove_user_role_flow(actual_roles)
        if not role_name:
            return

    try:
        # revalidation côté ctrl, source de vérité
        _ = ctrl.get_user(int(user_id))
        role = role_ctrl.get_role_by_name(role_name)

        confirmed = Validations.confirm_action(
            f"Êtes-vous sûr de vouloir supprimer le rôle '{role_name}' de l'utilisateur ?"
        )

        if not confirmed:
            return

        ctrl.remove_role(user_id, role["id"])
        if view.app_state:
            view.app_state.set_success_message(
                "Le rôle a été retiré de l'utilisateur avec succès."
            )

    except Exception as e:
        view.app_state.set_error_message(str(e))
        return
