import click
from crm.cli.db_commands import init_db, reset_hard
from crm.cli.auth_commands import login_cmd, logout_cmd
from crm.controllers.main_controller import MainController
from crm.utils.sentry_config import (
    init_sentry,
    install_global_exception_hook,
)

init_sentry()
install_global_exception_hook()


@click.group()
def cli():
    """CLI technique (reset, init, login/logout)"""
    pass


# Commandes DB
cli.add_command(init_db)
cli.add_command(reset_hard)

# Commandes d'auth
cli.add_command(login_cmd)
cli.add_command(logout_cmd)


@cli.command("run")
def run_app():
    """Lance l'application CRM"""
    app = MainController()
    app.run()


if __name__ == "__main__":
    cli()
