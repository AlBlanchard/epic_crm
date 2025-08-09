# crm/cli.py
import json
import sys
from getpass import getpass
from datetime import datetime

import click

from ..database import SessionLocal

# Controllers
from ..controllers.auth_controller import AuthController
from ..controllers.user_controller import UserController
from ..controllers.role_controller import RoleController
from ..controllers.client_controller import ClientController
from ..controllers.contract_controller import ContractController
from ..controllers.event_controller import EventController


# ---------- Helpers ----------
def _echo_json(obj):
    click.echo(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def _with_session(controller_cls):
    """Context manager helper to open/close a session for each command."""

    def wrapper(func):
        @click.pass_context
        def inner(ctx, *args, **kwargs):
            with SessionLocal() as session:
                ctrl = controller_cls(session=session)
                return func(ctrl, *args, **kwargs)

        return inner

    return wrapper


# ---------- Root group ----------
@click.group()
def cli():
    """Epic CRM CLI — tests rapides des controllers."""
    pass


# =======================
# AUTH
# =======================
@cli.group()
def auth():
    """Authentification (login / me / refresh / logout)."""
    pass


@auth.command("login")
@_with_session(AuthController)
def auth_login(ctrl: AuthController):
    """S'authentifie et sauvegarde le token access localement."""
    username = click.prompt("Nom d'utilisateur")
    password = getpass("Mot de passe : ")
    try:
        res = ctrl.login(username, password)
        _echo_json(res)
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@auth.command("me")
@_with_session(AuthController)
def auth_me(ctrl: AuthController):
    """Affiche le profil de l'utilisateur courant."""
    try:
        _echo_json(ctrl.me())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@auth.command("refresh")
@_with_session(AuthController)
@click.option("--refresh-token", prompt=True, help="Collez ici le refresh token.")
def auth_refresh(ctrl: AuthController, refresh_token: str):
    """Rafraîchit l'access token en utilisant un refresh token."""
    try:
        _echo_json(ctrl.refresh(refresh_token))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@auth.command("logout")
@_with_session(AuthController)
@click.option(
    "--refresh-token", default=None, help="(Optionnel) refresh token à révoquer aussi."
)
def auth_logout(ctrl: AuthController, refresh_token: str | None):
    """Révoque l'access (et éventuellement refresh) et supprime le fichier local."""
    try:
        _echo_json(ctrl.logout(refresh_token))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


# =======================
# USERS
# =======================
@cli.group()
def users():
    """Gestion des utilisateurs."""
    pass


@users.command("list")
@_with_session(UserController)
def users_list(ctrl: UserController):
    try:
        _echo_json(ctrl.list_users())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@users.command("get")
@_with_session(UserController)
@click.argument("user_id", type=int)
def users_get(ctrl: UserController, user_id: int):
    try:
        _echo_json(ctrl.get_user(user_id))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@users.command("me")
@_with_session(UserController)
def users_me(ctrl: UserController):
    try:
        _echo_json(ctrl.me())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@users.command("create")
@_with_session(UserController)
@click.option("--username", prompt=True)
@click.option("--email", prompt=True)
@click.option("--employee-number", prompt=True, type=int)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
def users_create(
    ctrl: UserController, username: str, email: str, employee_number: int, password: str
):
    try:
        data = {
            "username": username,
            "email": email,
            "employee_number": employee_number,
            "password": password,
        }
        _echo_json(ctrl.create_user(data))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@users.command("update")
@_with_session(UserController)
@click.argument("user_id", type=int)
@click.option("--username", default=None)
@click.option("--email", default=None)
@click.option("--employee-number", type=int, default=None)
@click.option("--password", default=None, hide_input=True)
def users_update(
    ctrl: UserController,
    user_id: int,
    username: str | None,
    email: str | None,
    employee_number: int | None,
    password: str | None,
):
    try:
        data = {}
        if username is not None:
            data["username"] = username
        if email is not None:
            data["email"] = email
        if employee_number is not None:
            data["employee_number"] = employee_number
        if password:
            data["password"] = password
        _echo_json(ctrl.update_user(user_id, data))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@users.command("change-password")
@_with_session(UserController)
@click.argument("user_id", type=int)
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
def users_change_pwd(ctrl: UserController, user_id: int, password: str):
    try:
        ctrl.change_password(user_id, password)
        click.echo("Mot de passe mis à jour.")
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@users.command("delete")
@_with_session(UserController)
@click.argument("user_id", type=int)
def users_delete(ctrl: UserController, user_id: int):
    try:
        ctrl.delete_user(user_id)
        click.echo("Utilisateur supprimé.")
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@users.command("add-role")
@_with_session(UserController)
@click.argument("user_id", type=int)
@click.argument("role_name", type=str)
def users_add_role(ctrl: UserController, user_id: int, role_name: str):
    try:
        ctrl.add_role(user_id, role_name)
        click.echo("Rôle ajouté.")
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@users.command("remove-role")
@_with_session(UserController)
@click.argument("user_id", type=int)
@click.argument("role_name", type=str)
def users_remove_role(ctrl: UserController, user_id: int, role_name: str):
    try:
        ctrl.remove_role(user_id, role_name)
        click.echo("Rôle retiré.")
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


# =======================
# ROLES
# =======================
@cli.group()
def roles():
    """Gestion des rôles."""
    pass


@roles.command("list")
@_with_session(RoleController)
def roles_list(ctrl: RoleController):
    try:
        _echo_json(ctrl.list_roles())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@roles.command("create")
@_with_session(RoleController)
@click.argument("name", type=str)
def roles_create(ctrl: RoleController, name: str):
    try:
        _echo_json(ctrl.create_role(name))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@roles.command("delete")
@_with_session(RoleController)
@click.argument("role_id", type=int)
@click.option(
    "--force", is_flag=True, help="Forcer la suppression même si assigné (admin)."
)
def roles_delete(ctrl: RoleController, role_id: int):
    try:
        ctrl.delete_role(role_id)
        click.echo("Rôle supprimé.")
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@roles.command("users")
@_with_session(RoleController)
@click.argument("role_name", type=str)
def roles_users(ctrl: RoleController, role_name: str):
    try:
        _echo_json(ctrl.users_with_role(role_name))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


# =======================
# CLIENTS
# =======================
@cli.group()
def clients():
    """Gestion des clients."""
    pass


@clients.command("list")
@_with_session(ClientController)
def clients_list(ctrl: ClientController):
    try:
        _echo_json(ctrl.list_clients())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@clients.command("my")
@_with_session(ClientController)
def clients_my(ctrl: ClientController):
    try:
        _echo_json(ctrl.list_my_clients())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@clients.command("create")
@_with_session(ClientController)
@click.option("--full-name", prompt=True)
@click.option("--email", prompt=True)
@click.option("--phone", default="", show_default=True)
@click.option("--company-name", default="", show_default=True)
@click.option(
    "--sales-contact-id", type=int, default=None, help="Par défaut : vous-même."
)
def clients_create(
    ctrl: ClientController,
    full_name: str,
    email: str,
    phone: str,
    company_name: str,
    sales_contact_id: int | None,
):
    try:
        data = {
            "full_name": full_name,
            "email": email,
            "phone": phone or None,
            "company_name": company_name or None,
        }
        if sales_contact_id is not None:
            data["sales_contact_id"] = sales_contact_id
        _echo_json(ctrl.create_client(data))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@clients.command("update")
@_with_session(ClientController)
@click.argument("client_id", type=int)
@click.option("--full-name", default=None)
@click.option("--email", default=None)
@click.option("--phone", default=None)
@click.option("--company-name", default=None)
@click.option("--sales-contact-id", type=int, default=None)
def clients_update(
    ctrl: ClientController,
    client_id: int,
    full_name: str | None,
    email: str | None,
    phone: str | None,
    company_name: str | None,
    sales_contact_id: int | None,
):
    try:
        data = {}
        if full_name is not None:
            data["full_name"] = full_name
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
        if company_name is not None:
            data["company_name"] = company_name
        if sales_contact_id is not None:
            data["sales_contact_id"] = sales_contact_id
        _echo_json(ctrl.update_client(client_id, data))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@clients.command("delete")
@_with_session(ClientController)
@click.argument("client_id", type=int)
@click.option("--force", is_flag=True, help="Admin peut forcer si contrats existants.")
def clients_delete(ctrl: ClientController, client_id: int, force: bool):
    try:
        ctrl.delete_client(client_id, force=force)
        click.echo("Client supprimé.")
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@clients.command("assign")
@_with_session(ClientController)
@click.argument("client_id", type=int)
@click.argument("sales_contact_id", type=int)
def clients_assign(ctrl: ClientController, client_id: int, sales_contact_id: int):
    try:
        _echo_json(ctrl.assign_sales_contact(client_id, sales_contact_id))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@clients.command("search")
@_with_session(ClientController)
@click.argument("term", type=str)
def clients_search(ctrl: ClientController, term: str):
    try:
        _echo_json(ctrl.search(term))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


# =======================
# CONTRACTS
# =======================
@cli.group()
def contracts():
    """Gestion des contrats."""
    pass


@contracts.command("list")
@_with_session(ContractController)
def contracts_list(ctrl: ContractController):
    try:
        _echo_json(ctrl.list_contracts())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@contracts.command("my")
@_with_session(ContractController)
def contracts_my(ctrl: ContractController):
    try:
        _echo_json(ctrl.list_my_contracts())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@contracts.command("create")
@_with_session(ContractController)
@click.option("--client-id", prompt=True, type=int)
@click.option("--amount-total", prompt=True, type=float)
@click.option("--amount-due", prompt=True, type=float)
@click.option("--is-signed", is_flag=True, default=False, show_default=True)
@click.option(
    "--sales-contact-id", type=int, default=None, help="Par défaut : vous-même (sales)."
)
def contracts_create(
    ctrl: ContractController,
    client_id: int,
    amount_total: float,
    amount_due: float,
    is_signed: bool,
    sales_contact_id: int | None,
):
    try:
        data = {
            "client_id": client_id,
            "amount_total": amount_total,
            "amount_due": amount_due,
            "is_signed": bool(is_signed),
        }
        if sales_contact_id is not None:
            data["sales_contact_id"] = sales_contact_id
        _echo_json(ctrl.create_contract(data))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@contracts.command("update")
@_with_session(ContractController)
@click.argument("contract_id", type=int)
@click.option("--client-id", type=int, default=None)
@click.option("--sales-contact-id", type=int, default=None)
@click.option("--amount-total", type=float, default=None)
@click.option("--amount-due", type=float, default=None)
@click.option("--is-signed", type=bool, default=None)
def contracts_update(
    ctrl: ContractController,
    contract_id: int,
    client_id: int | None,
    sales_contact_id: int | None,
    amount_total: float | None,
    amount_due: float | None,
    is_signed: bool | None,
):
    try:
        data = {}
        if client_id is not None:
            data["client_id"] = client_id
        if sales_contact_id is not None:
            data["sales_contact_id"] = sales_contact_id
        if amount_total is not None:
            data["amount_total"] = amount_total
        if amount_due is not None:
            data["amount_due"] = amount_due
        if is_signed is not None:
            data["is_signed"] = is_signed
        _echo_json(ctrl.update_contract(contract_id, data))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@contracts.command("delete")
@_with_session(ContractController)
@click.argument("contract_id", type=int)
@click.option(
    "--force", is_flag=True, help="Admin peut forcer la suppression d'un signé."
)
def contracts_delete(ctrl: ContractController, contract_id: int, force: bool):
    try:
        ctrl.delete_contract(contract_id, force=force)
        click.echo("Contrat supprimé.")
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@contracts.command("mark-signed")
@_with_session(ContractController)
@click.argument("contract_id", type=int)
@click.option("--signed/--not-signed", default=True, show_default=True)
def contracts_mark_signed(ctrl: ContractController, contract_id: int, signed: bool):
    try:
        _echo_json(ctrl.mark_signed(contract_id, is_signed=signed))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


# =======================
# EVENTS
# =======================
@cli.group()
def events():
    """Gestion des événements."""
    pass


@events.command("list")
@_with_session(EventController)
def events_list(ctrl: EventController):
    try:
        _echo_json(ctrl.list_events())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@events.command("my")
@_with_session(EventController)
def events_my(ctrl: EventController):
    try:
        _echo_json(ctrl.list_my_events())
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@events.command("create")
@_with_session(EventController)
@click.option("--contract-id", prompt=True, type=int)
@click.option("--date-start", prompt="Date de début (YYYY-MM-DD HH:MM)", type=str)
@click.option("--date-end", prompt="Date de fin (YYYY-MM-DD HH:MM)", type=str)
@click.option("--location", default="", show_default=True)
@click.option("--attendees", type=int, default=0, show_default=True)
@click.option("--notes", default="", show_default=True)
@click.option(
    "--support-contact-id",
    type=int,
    default=None,
    help="Par défaut : vous-même (support).",
)
def events_create(
    ctrl: EventController,
    contract_id: int,
    date_start: str,
    date_end: str,
    location: str,
    attendees: int,
    notes: str,
    support_contact_id: int | None,
):
    try:
        start = datetime.fromisoformat(date_start)
        end = datetime.fromisoformat(date_end)
        data = {
            "contract_id": contract_id,
            "date_start": start,
            "date_end": end,
            "location": location or None,
            "attendees": attendees or None,
            "notes": notes or None,
        }
        if support_contact_id is not None:
            data["support_contact_id"] = support_contact_id
        _echo_json(ctrl.create_event(data))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@events.command("update")
@_with_session(EventController)
@click.argument("event_id", type=int)
@click.option("--contract-id", type=int, default=None)
@click.option("--support-contact-id", type=int, default=None)
@click.option("--date-start", type=str, default=None)
@click.option("--date-end", type=str, default=None)
@click.option("--location", type=str, default=None)
@click.option("--attendees", type=int, default=None)
@click.option("--notes", type=str, default=None)
def events_update(
    ctrl: EventController,
    event_id: int,
    contract_id: int | None,
    support_contact_id: int | None,
    date_start: str | None,
    date_end: str | None,
    location: str | None,
    attendees: int | None,
    notes: str | None,
):
    try:
        data = {}
        if contract_id is not None:
            data["contract_id"] = contract_id
        if support_contact_id is not None:
            data["support_contact_id"] = support_contact_id
        if date_start is not None:
            data["date_start"] = datetime.fromisoformat(date_start)
        if date_end is not None:
            data["date_end"] = datetime.fromisoformat(date_end)
        if location is not None:
            data["location"] = location
        if attendees is not None:
            data["attendees"] = attendees
        if notes is not None:
            data["notes"] = notes
        _echo_json(ctrl.update_event(event_id, data))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@events.command("delete")
@_with_session(EventController)
@click.argument("event_id", type=int)
def events_delete(ctrl: EventController, event_id: int):
    try:
        ctrl.delete_event(event_id)
        click.echo("Événement supprimé.")
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


@events.command("assign")
@_with_session(EventController)
@click.argument("event_id", type=int)
@click.argument("support_user_id", type=int)
def events_assign(ctrl: EventController, event_id: int, support_user_id: int):
    try:
        _echo_json(ctrl.assign_support(event_id, support_user_id))
    except Exception as e:
        click.echo(f"Erreur: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
