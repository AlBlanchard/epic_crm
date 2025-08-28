import click
import sys
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect
from crm.database import Base, engine, SessionLocal
from ..models.role import Role
from ..models.user import User
from ..models.client import Client  # Import nécessaire pour la création des tables
from ..models.contract import Contract  # Import nécessaire pour la création des tables
from ..models.event import Event  # Import nécessaire pour la création des tables
from sqlalchemy import text
from ..auth.permission import Permission
from ..controllers.user_controller import UserController
from config.settings import DATABASE
from config.settings import get_admin_url
from sqlalchemy import create_engine, text
from ..utils.validations import Validations


@click.group(name="db-cli")
def db_cli():
    """Commandes liées à la base de données."""
    pass


def _bootstrap_database():

    admin_engine = create_engine(get_admin_url(), isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE USER {DATABASE['user']} WITH PASSWORD '{DATABASE['password']}'"
            )
        )
        conn.execute(
            text(f"CREATE DATABASE {DATABASE['database']} OWNER {DATABASE['user']}")
        )


def _database_exists():
    """Vérifie si la base de données existe et contient des tables."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return len(tables) > 0
    except Exception:
        return False


def _create_initial_data():
    """Crée les rôles de base et l'utilisateur admin."""
    Base.metadata.create_all(bind=engine)
    click.echo("Base de données créée.")

    # Saisie interactive des informations admin
    click.echo("\n=== Configuration de l'utilisateur admin ===")
    username = click.prompt("Nom d'utilisateur admin", default="admin")
    email = click.prompt("Email admin", default="admin@example.com")
    try:
        Validations.validate_email(email)
    except ValueError as ve:
        click.echo(f"{ve} Email par défault utilisé (admin@example.com). Vous pouvez le changer plus tard.")
        email = "admin@example.com"
    password = click.prompt(
        "Mot de passe admin", hide_input=True, confirmation_prompt=True
    )

    with SessionLocal() as session:
        try:
            # Création des rôles de base
            roles = {}
            for role_name in ["admin", "gestion", "commercial", "support"]:
                role = Role(name=role_name)
                session.add(role)
                roles[role_name] = role
            session.flush()

            # Création de l'utilisateur admin
            admin = User(employee_number=1, username=username, email=email)
            admin.set_password(password)
            session.add(admin)
            session.flush()

            # Attribution du rôle admin
            admin.add_role(roles["admin"], session)

            session.commit()
            click.echo("Rôles créés et utilisateur admin ajouté avec succès.")

        except IntegrityError:
            session.rollback()
            click.echo("Un problème est survenu (doublons ?).")
        except Exception as e:
            session.rollback()
            click.echo(f"Erreur lors de la création des données : {e}")


def _terminate_other_sessions(conn):
    # tue toutes les sessions de la base courante sauf la nôtre
    conn.execute(
        text(
            """
        SELECT pg_terminate_backend(pid)
        FROM pg_stat_activity
        WHERE datname = current_database()
        AND pid <> pg_backend_pid();
    """
        )
    )


@click.command("init")
@click.pass_context
def init_db(ctx: click.Context):
    """Initialise la base de données."""

    _bootstrap_database()

    # Vérification si la base existe déjà
    if _database_exists():
        click.echo("")
        click.echo("-- ! Une base de données existe déjà ! --")
        click.echo("")
        click.echo("Pour réinitialiser complètement la base de données, utilisez :")
        click.echo("-> db-cli reset-hard")
        click.echo("")
        return

    _create_initial_data()


@click.command("reset-hard")
@click.confirmation_option(
    prompt="Détruire le schéma public (DROP SCHEMA public CASCADE) puis le recréer ?"
)
@click.pass_context
def reset_hard(ctx: click.Context):

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if not Permission.is_admin(me):
        sys.exit("Accès refusé.")

    engine.dispose()

    # Exécute la nuke (BOOM)
    with engine.connect() as raw:
        raw = raw.execution_options(isolation_level="AUTOCOMMIT")
        raw.execute(text("SET lock_timeout = '3s'"))
        raw.execute(text("SET statement_timeout = '30s'"))

        # tuer les autres connexions au DB
        _terminate_other_sessions(raw)

        # drop/recreate schéma
        raw.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        raw.execute(text("CREATE SCHEMA public"))
        raw.execute(text("SET search_path TO public"))

    # Et la DB renait de ses cendres...
    Base.metadata.create_all(bind=engine)
    _create_initial_data()

    click.secho("Reset hard terminé", fg="green")
