import click
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect
from crm.database import Base, engine, SessionLocal
from ..models.role import Role
from ..models.user import User
from ..models.client import Client  # Import nécessaire pour la création des tables
from ..models.contract import Contract  # Import nécessaire pour la création des tables
from ..models.event import Event  # Import nécessaire pour la création des tables
from sqlalchemy import text


@click.group(name="db-cli")
def db_cli():
    """Commandes liées à la base de données."""
    pass


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
    password = click.prompt(
        "Mot de passe admin", hide_input=True, confirmation_prompt=True
    )

    with SessionLocal() as session:
        try:
            # Création des rôles de base
            roles = {}
            for role_name in ["admin", "management", "sales", "support"]:
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


@db_cli.command("init")
@click.option(
    "--force", is_flag=True, help="Force l'initialisation même si la DB existe"
)
def init_db(force):
    """Initialise la base de données."""

    # Vérification si la base existe déjà
    if _database_exists() and not force:
        click.echo("")
        click.echo("-- ! Une base de données existe déjà ! --")
        click.echo("")
        click.echo("Pour réinitialiser complètement la base de données, utilisez :")
        click.echo("-> db-cli reset")
        click.echo("")
        return

    _create_initial_data()


@db_cli.command("reset")
def reset_db():
    """Réinitialise la base de données et crée les rôles + un admin par défaut."""
    confirm = click.confirm(
        "Cette opération va supprimer et recréer toute la base, c'est irréversible. Continuer ?",
        default=False,
    )
    if not confirm:
        click.echo("Opération annulée.")
        return

    # Drop puis recrée toutes les tables
    click.echo("Suppression de la base de données...")
    Base.metadata.drop_all(bind=engine)

    _create_initial_data()


@db_cli.command("reset-hard")
@click.confirmation_option(
    prompt="Détruire le schéma public (DROP SCHEMA public CASCADE) puis le recréer ?"
)
def reset_hard():
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    Base.metadata.create_all(bind=engine)
    _create_initial_data()
    click.secho("Reset hard terminé", fg="green")
