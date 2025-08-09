import click
from ..models.user import User
from ..models.user_role import UserRole
from crm.database import SessionLocal
from getpass import getpass
from pathlib import Path
from ..data_reader import DataReader
from ..controllers.user_controller import UserController
from ..controllers.role_controller import RoleController

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


@user_cli.command(name="list-users")
def list_users():
    """Affiche tous les utilisateurs (si rôle admin)."""
    with SessionLocal() as session:
        try:
            reader = DataReader(session)
            users = reader.get_all_users()
            for user in users:
                click.echo(f"{user.id} - {user.username}")
        except Exception as e:
            click.echo(f"Erreur : {e}")


@user_cli.command(name="list-roles")
def list_roles():
    """Affiche tous les rôles (si rôle admin)."""
    with SessionLocal() as session:
        try:
            reader = DataReader(session)
            roles = reader.get_all_roles()
            for role in roles:
                click.echo(f"{role.id} - {role.name}")
        except Exception as e:
            click.echo(f"Erreur : {e}")


@user_cli.command(name="hash-password")
def hashpassword():
    """Génère un hash pour un mot de passe."""
    password = getpass("Entrez le mot de passe à hasher : ")
    user = User()
    hashed_password = user.set_password(password)
    click.echo(f"Hash du mot de passe : {hashed_password}")


@user_cli.command(name="create-user")
def create_user():
    """
    Crée un utilisateur de test via les controllers :
    - demande username / email / employee_number / password
    - liste les rôles existants (via RoleController)
    - crée l'utilisateur (UserController.create_user)
    - assigne le rôle choisi (UserController.add_role)
    """
    username = click.prompt("Nom d'utilisateur pour le test")
    email = click.prompt("Email pour le test")
    employee_number = click.prompt("Numéro d'employé pour le test", type=int)
    password = getpass("Mot de passe pour le test : ")

    with SessionLocal() as session:
        print("Création de l'utilisateur de test...")
        users = UserController(session=session)
        print("Chargement des rôles...")
        roles = RoleController(session=session)

        try:
            # liste les rôles existants (admin requis)
            all_roles = roles.list_roles()
            if not all_roles:
                click.echo("Aucun rôle n'existe encore. Créez-en d'abord (admin).")
                return

            click.echo("Rôles disponibles :")
            for r in all_roles:
                click.echo(f"{r['id']} - {r['name']}")

            chosen_id = click.prompt(
                "Sélectionner le role_id souhaité", type=int, default=all_roles[0]["id"]
            )
            role_row = next((r for r in all_roles if r["id"] == chosen_id), None)
            if not role_row:
                click.echo(f"Rôle {chosen_id} introuvable.")
                return

            chosen_role_name = role_row["name"]

            # créer l'utilisateur (admin requis)
            print("Création de l'utilisateur...")
            new_user = users.create_user(
                {
                    "username": username,
                    "email": email,
                    "employee_number": employee_number,
                    "password": password,  # hashé par le modèle côté CRUD
                }
            )

            # 3) assigner le rôle
            print("Assignation du rôle...")
            users.add_role(new_user["id"], chosen_role_name)

            click.echo(
                f"Utilisateur de test créé : {new_user['username']} (id={new_user['id']})"
            )
            click.echo(f"Rôle assigné : {chosen_role_name}")

        except PermissionError as e:
            click.echo(f"Permission refusée : {e}")
        except ValueError as e:
            click.echo(f"Erreur : {e}")
        except Exception as e:
            click.echo(f"Erreur inattendue : {e}")
