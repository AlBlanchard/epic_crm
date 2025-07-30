import click
import json

from .auth.auth import Authentication
from .auth.jti_manager import JTIManager
from crm.models import User
from crm.database import SessionLocal  # Ton sessionmaker
from getpass import getpass
from pathlib import Path


@click.group()
def cli():
    pass


ACCESS_TOKEN_PATH = Path("access_token.jwt")
REFRESH_TOKEN_PATH = Path("refresh_token.jwt")


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

        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Enregistrement des tokens dans des fichiers séparés
        ACCESS_TOKEN_PATH.write_text(access_token)
        REFRESH_TOKEN_PATH.write_text(refresh_token)

        # Stockage des jti dans le JTIManager
        access_payload = Authentication.verify_token(access_token)
        refresh_payload = Authentication.verify_token(refresh_token)

        jti_store = JTIManager()
        jti_store.add(access_payload["jti"])
        jti_store.add(refresh_payload["jti"])

        click.echo(
            "Authentification réussie. Les tokens ont été générés et enregistrés."
        )


@click.command()
def logout():
    """
    Déconnecte l'utilisateur : révoque le token et le supprime localement.
    """
    token = Authentication.load_token()
    if not token:
        click.echo("Aucun token trouvé. Vous êtes peut-être déjà déconnecté.")
        return

    try:
        payload = Authentication.verify_token(token)
        jti = payload.get("jti")

        if jti:
            jti_store = JTIManager()
            jti_store.revoke(jti)
            click.echo("Le token a été révoqué.")
        else:
            click.echo("Token sans identifiant unique (jti). Révocation impossible.")

        # Supprimer le fichier local
        ACCESS_TOKEN_PATH.unlink(missing_ok=True)
        REFRESH_TOKEN_PATH.unlink(missing_ok=True)
        click.echo("Déconnexion réussie.")

    except ValueError as e:
        click.echo(f"Erreur : {e}")
        ACCESS_TOKEN_PATH.unlink(missing_ok=True)
        click.echo("Fichier token supprimé malgré l'erreur.")


cli.add_command(logout)


@click.command()
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


cli.add_command(refresh)
