import click
from rich.console import Console
from ..database import SessionLocal
from ..controllers.user_controller import UserController
from ..controllers.role_controller import RoleController
from getpass import getpass


class UserView:

    @click.command(name="create-user")
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
                    "Sélectionner le role_id souhaité",
                    type=int,
                    default=all_roles[0]["id"],
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
