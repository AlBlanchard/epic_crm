import click
from rich.console import Console

from crm.views.auth_view import AuthView
from crm.views.menu_view import menu_cmd
from crm.cli.auth_commands import login_cmd, logout_cmd
from crm.cli.user_commands import (
    create_user_cmd,
    list_users_cmd,
    update_user_cmd,
    delete_user_cmd,
    update_user_password_cmd,
    update_user_infos_cmd,
    add_user_role_cmd,
    remove_user_role_cmd,
)
from crm.cli.client_commands import (
    create_client_cmd,
    list_clients_cmd,
    update_client_cmd,
    update_sales_contact_cmd,
    delete_client_cmd,
)
from crm.cli.contract_commands import (
    create_contract_cmd,
    list_contracts_cmd,
    sign_contract_cmd,
    update_contract_amount_cmd,
    delete_contract_cmd,
)
from crm.cli.event_commands import (
    create_event_cmd,
    list_events_cmd,
    update_event_cmd,
    add_event_note_cmd,
    delete_note_cmd,
    update_support_cmd,
    delete_event_cmd,
)
from crm.utils.app_state import AppState


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    """
    CRM CLI — vérifie l'auth à l'ouverture, puis lance un menu par défaut.
    Les objets partagés (console, app_state, vues) sont stockés dans ctx.obj.
    """
    # Contexte partagé
    ctx.ensure_object(dict)
    if "console" not in ctx.obj:
        ctx.obj["console"] = Console()
    if "app_state" not in ctx.obj:
        ctx.obj["app_state"] = AppState

    console: Console = ctx.obj["console"]

    # Instancie AuthView une seule fois et la stocke
    if "auth_view" not in ctx.obj:
        ctx.obj["auth_view"] = AuthView()
    auth_view: AuthView = ctx.obj["auth_view"]

    # Laisse passer login/logout sans authentification préalable
    if ctx.invoked_subcommand in {"login", "logout"}:
        return

    # Vérifie l'auth sinon
    if not auth_view.ensure_authenticated():
        console.print("[bold yellow]Connexion requise.[/bold yellow]")
        ctx.invoke(login_cmd)

    # Si aucune sous-commande, on lance le menu principal
    if ctx.invoked_subcommand is None:
        ctx.invoke(menu_cmd)


# --- Enregistrement des commandes ---
# Auth
@click.pass_context
def _bind_auth(ctx: click.Context):
    # utilitaire pour attacher d’autres vues plus tard
    return ctx


# Commandes d'auth (méthodes Click sur l'instance)
cli.add_command(login_cmd)  # accès via: cli login
cli.add_command(logout_cmd)  # accès via: cli logout

# Menu principal (fonction Click indépendante)
cli.add_command(menu_cmd)  # accès via: cli menu

# Autres commandes réutilisables depuis le menu ou en direct

# -- Users--
cli.add_command(create_user_cmd)
cli.add_command(list_users_cmd)
cli.add_command(update_user_cmd)
cli.add_command(update_user_password_cmd)
cli.add_command(delete_user_cmd)
cli.add_command(update_user_infos_cmd)
cli.add_command(update_user_password_cmd)
cli.add_command(add_user_role_cmd)
cli.add_command(remove_user_role_cmd)

# -- Clients--
cli.add_command(create_client_cmd)
cli.add_command(list_clients_cmd)
cli.add_command(update_client_cmd)
cli.add_command(update_sales_contact_cmd)
cli.add_command(delete_client_cmd)

# -- Contracts--
cli.add_command(create_contract_cmd)
cli.add_command(list_contracts_cmd)
cli.add_command(sign_contract_cmd)
cli.add_command(update_contract_amount_cmd)
cli.add_command(delete_contract_cmd)

# -- Events--
cli.add_command(create_event_cmd)
cli.add_command(list_events_cmd)
cli.add_command(update_event_cmd)
cli.add_command(add_event_note_cmd)
cli.add_command(delete_note_cmd)
cli.add_command(update_support_cmd)
cli.add_command(delete_event_cmd)


if __name__ == "__main__":
    cli()
