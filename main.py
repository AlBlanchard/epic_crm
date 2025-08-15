import click
from rich.console import Console

from crm.views.auth_view import AuthView
from crm.views.menu_view import menu_cmd
from crm.views.user_view import create_user_cmd, list_users_cmd, update_user_cmd
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
        ctx.invoke(auth_view.login_cmd)

    # Si aucune sous-commande, on lance le menu principal
    if ctx.invoked_subcommand is None:
        ctx.invoke(menu_cmd)


# --- Enregistrement des commandes ---
# Auth
@click.pass_context
def _bind_auth(ctx: click.Context):
    # utilitaire si tu veux attacher d’autres vues plus tard
    return ctx


# Commandes d'auth (méthodes Click sur l'instance)
cli.add_command(AuthView.login_cmd)  # accès via: cli login
cli.add_command(AuthView.logout_cmd)  # accès via: cli logout

# Menu principal (fonction Click indépendante)
cli.add_command(menu_cmd)  # accès via: cli menu

# Exemple : autres commandes réutilisables depuis le menu OU en direct
# (si tu exposes create_user_cmd comme fonction Click)
cli.add_command(create_user_cmd)  # accès via: cli create-user
cli.add_command(list_users_cmd)
cli.add_command(update_user_cmd)


if __name__ == "__main__":
    cli()
