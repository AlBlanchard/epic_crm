import click
from .db_commands import db_cli
from .auth_commands import auth_cli


@click.group()
def cli():
    """Interface CLI Epic Events."""
    pass


# Regroupe les commandes par sous-groupes
cli.add_command(db_cli)
cli.add_command(auth_cli)

if __name__ == "__main__":
    cli()
