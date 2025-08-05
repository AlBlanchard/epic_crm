import click
from crm.models import User
from crm.database import SessionLocal
from getpass import getpass
from pathlib import Path
from ..data_reader import DataReader

ACCESS_TOKEN_PATH = Path("access_token.jwt")
REFRESH_TOKEN_PATH = Path("refresh_token.jwt")


@click.group(name="user-cli")
def user_cli():
    """Commandes liées aux utilisateurs."""
    pass


@user_cli.command(name="list-clients")
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


@user_cli.command(name="list-contracts")
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


@user_cli.command(name="list-events")
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


@user_cli.command(name="hash-password")
def hashpassword():
    """Génère un hash pour un mot de passe."""
    password = getpass("Entrez le mot de passe à hasher : ")
    user = User()
    hashed_password = user.set_password(password)
    click.echo(f"Hash du mot de passe : {hashed_password}")


@user_cli.command(name="create-test-user")
def create_test_user():
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
