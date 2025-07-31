import click
import json

from .auth.auth import Authentication
from .auth.jti_manager import JTIManager
from crm.models import User
from crm.database import SessionLocal  # Ton sessionmaker
from getpass import getpass
from pathlib import Path
from .data_reader import DataReader
from .auth.config import TOKEN_PATH


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
        access_payload = Authentication.verify_token_without_jti(access_token)
        refresh_payload = Authentication.verify_token_without_jti(refresh_token)

        jti_store = JTIManager()
        jti_store.add(access_payload["jti"])
        jti_store.add(refresh_payload["jti"])

        TOKEN_PATH.write_text(access_token)

        click.echo(
            "Authentification réussie. Les tokens ont été générés et enregistrés."
        )


@click.command()
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


@click.command()
def list_clients():
    """Affiche tous les clients (si rôle sales)."""
    with SessionLocal() as session:
        try:
            reader = DataReader(session)
            clients = reader.get_all_clients()
            for client in clients:
                click.echo(f"{client.id} - {client.name}")
        except Exception as e:
            click.echo(f"Erreur : {e}")


cli.add_command(list_clients)


@click.command()
def list_contracts():
    """Affiche tous les contrats (si rôle sales)."""
    with SessionLocal() as session:
        try:
            reader = DataReader(session)
            contracts = reader.get_all_contracts()
            for contract in contracts:
                click.echo(f"{contract.id} - {contract.description}")
        except Exception as e:
            click.echo(f"Erreur : {e}")


cli.add_command(list_contracts)


@click.command()
def list_events():
    """Affiche tous les événements (si rôle support)."""
    with SessionLocal() as session:
        try:
            reader = DataReader(session)
            events = reader.get_all_events()
            for event in events:
                click.echo(f"{event.id} - {event.title}")
        except Exception as e:
            click.echo(f"Erreur : {e}")


cli.add_command(list_events)


@click.command()
def hashpassword():
    """Génère un hash pour un mot de passe."""
    password = getpass("Entrez le mot de passe à hasher : ")
    user = User()
    hashed_password = user.set_password(password)
    click.echo(f"Hash du mot de passe : {hashed_password}")


cli.add_command(hashpassword)


@click.command()
def createtestuser():
    """Crée un utilisateur de test avec un mot de passe prédéfini."""
    username = click.prompt("Nom d'utilisateur pour le test")
    password = getpass("Mot de passe pour le test : ")
    email = click.prompt("Email pour le test : ")
    employee_number = click.prompt("Numéro d'employé pour le test : ")

    with SessionLocal() as session:
        user = User(username=username, email=email, employee_number=employee_number)
        user.set_password(password)
        session.add(user)
        session.commit()
        click.echo(f"Utilisateur de test créé : {user.username}")


cli.add_command(createtestuser)
