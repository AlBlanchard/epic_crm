import click
from .auth.auth import Authentication
from crm.models import User
from crm.database import SessionLocal  # Ton sessionmaker
from getpass import getpass
import json
from pathlib import Path

TOKEN_FILE = Path.home() / ".epic_token"


@click.group()
def cli():
    pass


@cli.command()
def login():
    """Authentifie un utilisateur et génère un token JWT."""
    username = click.prompt("Nom d'utilisateur")
    password = getpass("Mot de passe : ")

    with SessionLocal() as session:
        try:
            tokens = Authentication.authenticate_user(username, password, session)
        except ValueError:
            click.echo("Nom d'utilisateur ou mot de passe incorrect.")
            raise SystemExit(1)

        # Enregistre le token dans un fichier local
        TOKEN_FILE.write_text(json.dumps(tokens))
        click.echo("Authentification réussie.")
