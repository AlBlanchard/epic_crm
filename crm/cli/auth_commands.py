import click
from ..auth.auth import Authentication
from ..auth.jti_manager import JTIManager
from crm.models import User
from crm.database import SessionLocal
from getpass import getpass
from pathlib import Path
from ..data_reader import DataReader
from ..auth.config import TOKEN_PATH

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
        except ValueError:
            click.echo("Nom d'utilisateur ou mot de passe incorrect.")
            raise SystemExit(1)

        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Enregistrement des tokens dans des fichiers séparés
        ACCESS_TOKEN_PATH.write_text(access_token)
        REFRESH_TOKEN_PATH.write_text(refresh_token)

        # Stockage des jti dans le JTIManager
        access_payload = Authentication.verify_token_without_jti(access_token)
        refresh_payload = Authentication.verify_token_without_jti(refresh_token)

        jti_store = JTIManager()
        jti_store.add(access_payload["jti"])
        jti_store.add(refresh_payload["jti"])

        TOKEN_PATH.write_text(access_token)

        click.echo(
            "Authentification réussie. Les tokens ont été générés et enregistrés."
        )


@auth_cli.command("logout")
def logout():
    """
    Déconnecte l'utilisateur : révoque les tokens d'accès et de rafraîchissement, et les supprime localement.
    """
    jti_store = JTIManager()

    # Révoque le token d'accès
    if ACCESS_TOKEN_PATH.exists():
        try:
            token = ACCESS_TOKEN_PATH.read_text()
            payload = Authentication.verify_token(token)
            jti = payload.get("jti")
            if jti:
                jti_store.revoke(jti)
                click.echo("Token d'accès révoqué.")
        except Exception as e:
            click.echo(f"Erreur sur le token d'accès : {e}")

    # Révoque le token de rafraîchissement
    if REFRESH_TOKEN_PATH.exists():
        try:
            refresh_token = REFRESH_TOKEN_PATH.read_text()
            payload = Authentication.verify_token(refresh_token)
            jti = payload.get("jti")
            if jti:
                jti_store.revoke(jti)
                click.echo("Token de rafraîchissement révoqué.")
        except Exception as e:
            click.echo(f"Erreur sur le token de rafraîchissement : {e}")

    # Supprime les fichiers
    ACCESS_TOKEN_PATH.unlink(missing_ok=True)
    REFRESH_TOKEN_PATH.unlink(missing_ok=True)
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
