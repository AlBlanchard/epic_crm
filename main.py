import click
from rich.console import Console
from crm.views.auth_view import AuthView
from crm.utils.app_state import AppState
from crm.cli.db_commands import init_db, reset_hard
from crm.cli.auth_commands import login_cmd, logout_cmd
from crm.controllers.main_controller import MainController
from crm.utils.sentry_config import (
    init_sentry,
    install_global_exception_hook,
)

init_sentry()
install_global_exception_hook()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context):
    """
    CRM CLI — point d'entrée.
    - Commandes techniques : init, reset-hard, login, logout
    - Sinon : lance l'application via MainController
    """
    # Contexte partagé (console + état global)
    ctx.ensure_object(dict)
    if "console" not in ctx.obj:
        ctx.obj["console"] = Console()
    if "app_state" not in ctx.obj:
        ctx.obj["app_state"] = AppState

    # Si aucune commande CLI -> on lance l'application
    if ctx.invoked_subcommand is None:
        app = MainController()
        app.run()


# Commandes DB
cli.add_command(init_db)
cli.add_command(reset_hard)

# Commandes d'auth
cli.add_command(login_cmd)
cli.add_command(logout_cmd)


if __name__ == "__main__":
    cli()
