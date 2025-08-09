import click
from ..auth.auth import Authentication
from ..auth.jti_manager import JTIManager
from crm.database import SessionLocal
from getpass import getpass
from pathlib import Path
from ..auth.config import TOKEN_PATH

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

ACCESS_TOKEN_PATH = Path("access_token.jwt")
REFRESH_TOKEN_PATH = Path("refresh_token.jwt")


@click.group(name="auth-cli")
def auth_cli():
    """Commandes d'authentification."""
    pass


@auth_cli.command("login")
def login():
    """Authentifie un utilisateur et génère un token JWT."""
    username = click.prompt("Nom d'utilisateur")
    password = getpass("Mot de passe : ")

    with SessionLocal() as session:
        try:
            tokens = Authentication.authenticate_user(username, password, session)
            access = tokens["access_token"]
            refresh = tokens["refresh_token"]

        except ValueError as e:
            click.echo(f"Erreur : {str(e)}")
            raise SystemExit(1)

        # Enregistre le token d'accès dans un fichier
        Authentication.register_tokens_jti(access, refresh)
        Authentication.save_tokens(access, refresh)
        click.echo("Authentification réussie.")


@auth_cli.command("logout")
def logout():
    jti_store = JTIManager()
    pair = Authentication.load_tokens()
    if not pair:
        click.echo("Aucun token trouvé. Vous êtes peut-être déjà déconnecté.")
        return

    access, refresh = pair

    # Révoque access
    if access:
        try:
            payload = Authentication.verify_token_without_jti(access)
            jti = payload.get("jti")
            if jti:
                jti_store.revoke(jti)
                click.echo("Token d'accès révoqué.")
        except Exception as e:
            click.echo(f"Erreur sur le token d'accès : {e}")

    # Révoque refresh
    if refresh:
        try:
            payload = Authentication.verify_token_without_jti(refresh)
            jti = payload.get("jti")
            if jti:
                jti_store.revoke(jti)
                click.echo("Token de rafraîchissement révoqué.")
        except Exception as e:
            click.echo(f"Erreur sur le token de rafraîchissement : {e}")

    TOKEN_PATH.unlink(missing_ok=True)
    click.echo("Déconnexion réussie.")


@auth_cli.command("refresh")
def refresh():
    """
    Rafraîchit le token d'accès à partir du refresh_token stocké.
    """
    refresh_token_path = Path("refresh_token.jwt")

    if not refresh_token_path.exists():
        click.echo("Aucun token de rafraîchissement trouvé.")
        return

    refresh_token = refresh_token_path.read_text()

    try:
        new_access_token = Authentication.refresh_access_token(refresh_token)
        click.echo("Nouveau token d'accès généré et sauvegardé avec succès.")
    except ValueError as e:
        click.echo(f"Erreur lors du rafraîchissement : {e}")
