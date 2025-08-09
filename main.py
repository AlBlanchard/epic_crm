# main.py
import click
from rich.console import Console
from crm.views.auth_view import AuthView
from crm.views.menu_view import menu_cmd

console = Console()
auth_view = AuthView()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    CRM CLI — vérifie l'auth à l'ouverture, puis lance un menu par défaut.
    """
    # Autoriser les commandes d'auth sans check préalable
    if ctx.invoked_subcommand in {"login", "logout"}:
        return

    if not auth_view.ensure_authenticated():
        console.print("[bold yellow]Connexion requise.[/bold yellow]")
        ctx.invoke(auth_view.login_cmd)

    if ctx.invoked_subcommand is None:
        ctx.invoke(menu_cmd)


cli.add_command(auth_view.login_cmd)
cli.add_command(auth_view.logout_cmd)

if __name__ == "__main__":
    cli()
