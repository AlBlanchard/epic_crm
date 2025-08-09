# views/menu_view.py
import click
from rich.console import Console
from rich.table import Table
from typing import Optional
from ..database import SessionLocal

from .auth_view import AuthView
from ..controllers.client_controller import ClientController
from ..controllers.contract_controller import ContractController
from ..controllers.event_controller import EventController
from ..controllers.user_controller import UserController
from ..controllers.role_controller import RoleController

console = Console()
auth_view = AuthView()


def _prompt_optional_int(label: str):
    val = click.prompt(label, default="", show_default=False)
    val = val.strip()
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        console.print("[red]Veuillez entrer un entier valide ou laisser vide.[/red]")
        return _prompt_optional_int(label)


def _prompt_non_empty(label: str) -> str:
    """Validation minimale côté View : non vide. Le reste => Controller."""
    while True:
        val = click.prompt(label).strip()
        if val:
            return val
        console.print("[red]Ce champ est requis.[/red]")


def _prompt_optional(label: str) -> Optional[str]:
    val = click.prompt(label, default="", show_default=False)
    return val.strip() or None


def _print_table(title: str, columns: list[str], rows: list[dict]):
    table = Table(title=title)
    for col in columns:
        table.add_column(col, overflow="fold")
    for r in rows:
        table.add_row(*[str(r.get(c, "")) for c in columns])
    console.print(table)


@click.command(name="menu")
@click.pass_context
def menu_cmd(ctx):
    """
    Menu principal CRM (View).
    """
    client_ctrl = ClientController()
    contract_ctrl = ContractController()
    event_ctrl = EventController()
    user_ctrl = UserController()

    while True:
        console.print("\n[bold cyan]=== CRM — Menu principal ===[/bold cyan]")
        console.print("1. Clients")
        console.print("2. Contrats")
        console.print("3. Événements")
        console.print("4. Utilisateurs")
        console.print("5. Se déconnecter")
        console.print("6. Quitter")

        choice = click.prompt("Choix", type=int)

        try:
            if choice == 1:
                _menu_clients(client_ctrl)
            elif choice == 2:
                _menu_contracts(contract_ctrl)
            elif choice == 3:
                _menu_events(event_ctrl)
            elif choice == 4:
                _menu_users(user_ctrl)
            elif choice == 5:
                # Déconnexion locale (supprime le fichier de tokens)
                ctx.invoke(auth_view.logout_cmd)
                break
            elif choice == 6:
                console.print("👋 À bientôt.")
                break
            else:
                console.print("[red]Choix invalide[/red]")
        except Exception as e:
            # Catch-all View : le détail de validation reste côté Controller
            console.print(f"[red]Erreur : {e}[/red]")


# ----------------------
# Sous-menus (Clients)
# ----------------------
def _menu_clients(ctrl: ClientController):
    while True:
        console.print("\n[bold]— Clients —[/bold]")
        console.print("1. Créer un client")
        console.print("2. Lister les clients")
        console.print("3. Modifier un client")
        console.print("4. Supprimer un client")
        console.print("5. Retour")

        c = click.prompt("Choix", type=int)
        if c == 1:
            name = _prompt_non_empty("Nom")
            email = _prompt_non_empty("Email")
            phone = _prompt_optional("Téléphone")
            msg = ctrl.create_client(name=name, email=email, phone=phone)
            console.print(f"[green]{msg}[/green]")

        elif c == 2:
            rows = ctrl.list_clients()  # -> list[dict] ou list[Model]; adapte si besoin
            # Si tu renvoies des objets, transforme-les ici en dicts
            rows = [_asdict_client(r) for r in rows]
            _print_table(
                "Clients", ["id", "name", "email", "phone", "created_at"], rows
            )

        elif c == 3:
            client_id = click.prompt("ID du client", type=int)
            name = _prompt_optional("Nouveau nom (laisser vide pour ne pas changer)")
            email = _prompt_optional("Nouvel email (laisser vide pour ne pas changer)")
            phone = _prompt_optional(
                "Nouveau téléphone (laisser vide pour ne pas changer)"
            )
            msg = ctrl.update_client(client_id, name=name, email=email, phone=phone)
            console.print(f"[green]{msg}[/green]")

        elif c == 4:
            client_id = click.prompt("ID du client", type=int)
            confirm = click.confirm("Confirmer la suppression ?", default=False)
            if confirm:
                msg = ctrl.delete_client(client_id)
                console.print(f"[yellow]{msg}[/yellow]")

        elif c == 5:
            break
        else:
            console.print("[red]Choix invalide[/red]")


# ----------------------
# Sous-menus (Contrats)
# ----------------------
def _menu_contracts(ctrl: ContractController):
    while True:
        console.print("\n[bold]— Contrats —[/bold]")
        console.print("1. Créer un contrat")
        console.print("2. Lister les contrats")
        console.print("3. Modifier un contrat")
        console.print("4. Supprimer un contrat")
        console.print("5. Retour")

        c = click.prompt("Choix", type=int)
        if c == 1:
            client_id = click.prompt("ID client", type=int)
            title = _prompt_non_empty("Titre du contrat")
            amount = click.prompt("Montant (€)", type=float)
            status = _prompt_optional("Statut (draft/active/closed)")
            msg = ctrl.create_contract(
                client_id=client_id, title=title, amount=amount, status=status
            )
            console.print(f"[green]{msg}[/green]")

        elif c == 2:
            rows = ctrl.list_contracts()
            rows = [_asdict_contract(r) for r in rows]
            _print_table(
                "Contrats",
                ["id", "client_id", "title", "amount", "status", "created_at"],
                rows,
            )

        elif c == 3:
            contract_id = click.prompt("ID du contrat", type=int)
            title = _prompt_optional("Nouveau titre")
            amount = _prompt_optional("Nouveau montant (€)")
            status = _prompt_optional("Nouveau statut (draft/active/closed)")
            # Convertit amount si fourni
            amount_val = float(amount) if amount is not None else None
            msg = ctrl.update_contract(
                contract_id, title=title, amount=amount_val, status=status
            )
            console.print(f"[green]{msg}[/green]")

        elif c == 4:
            contract_id = click.prompt("ID du contrat", type=int)
            confirm = click.confirm("Confirmer la suppression ?", default=False)
            if confirm:
                msg = ctrl.delete_contract(contract_id)
                console.print(f"[yellow]{msg}[/yellow]")

        elif c == 5:
            break
        else:
            console.print("[red]Choix invalide[/red]")


# ----------------------
# Sous-menus (Événements)
# ----------------------
def _menu_events(ctrl: EventController):
    while True:
        console.print("\n[bold]— Événements —[/bold]")
        console.print("1. Créer un événement")
        console.print("2. Lister les événements")
        console.print("3. Modifier un événement")
        console.print("4. Supprimer un événement")
        console.print("5. Retour")

        c = click.prompt("Choix", type=int)
        if c == 1:
            contract_id = click.prompt("ID contrat", type=int)
            name = _prompt_non_empty("Nom de l'événement")
            date_str = _prompt_non_empty("Date (YYYY-MM-DD HH:MM)")
            location = _prompt_optional("Lieu")
            note = _prompt_optional("Note")
            msg = ctrl.create_event(
                contract_id=contract_id,
                name=name,
                date_str=date_str,
                location=location,
                note=note,
            )
            console.print(f"[green]{msg}[/green]")

        elif c == 2:
            rows = ctrl.list_events()
            rows = [_asdict_event(r) for r in rows]
            _print_table(
                "Événements",
                ["id", "contract_id", "name", "date", "location", "note", "created_at"],
                rows,
            )

        elif c == 3:
            event_id = click.prompt("ID de l'événement", type=int)
            name = _prompt_optional("Nouveau nom")
            date_str = _prompt_optional("Nouvelle date (YYYY-MM-DD HH:MM)")
            location = _prompt_optional("Nouveau lieu")
            note = _prompt_optional("Nouvelle note")
            msg = ctrl.update_event(
                event_id, name=name, date_str=date_str, location=location, note=note
            )
            console.print(f"[green]{msg}[/green]")

        elif c == 4:
            event_id = click.prompt("ID de l'événement", type=int)
            confirm = click.confirm("Confirmer la suppression ?", default=False)
            if confirm:
                msg = ctrl.delete_event(event_id)
                console.print(f"[yellow]{msg}[/yellow]")

        elif c == 5:
            break
        else:
            console.print("[red]Choix invalide[/red]")


# ----------------------
# Sous-menus (Utilisateurs)
# ----------------------
def _menu_users(ctrl: UserController):
    while True:
        console.print("\n[bold]— Utilisateurs —[/bold]")
        console.print("1. Créer un utilisateur")
        console.print("2. Lister les utilisateurs")
        console.print("3. Modifier un utilisateur")
        console.print("4. Supprimer un utilisateur")
        console.print("5. Retour")

        c = click.prompt("Choix", type=int)
        if c == 1:
            # --- Création d'utilisateur avec sélection d'un rôle existant ---
            username = _prompt_non_empty("Nom d'utilisateur")
            email = _prompt_non_empty("Email")
            employee_number = _prompt_optional_int("Numéro d'employé")
            password = click.prompt("Mot de passe", hide_input=True)

            # On ouvre une session pour alimenter les controllers (comme dans ton UserView)
            with SessionLocal() as session:
                users = UserController(session=session)
                roles = RoleController(session=session)

                try:
                    # 1) Lister les rôles existants
                    all_roles = (
                        roles.list_roles()
                    )  # attendu: list[dict] avec 'id' et 'name'
                    if not all_roles:
                        console.print(
                            "[yellow]Aucun rôle n'existe encore. Créez-en d'abord (admin).[/yellow]"
                        )
                        return

                    console.print("\n[bold]Rôles disponibles :[/bold]")
                    for r in all_roles:
                        console.print(f"- {r['id']} : {r['name']}")

                    # 2) Sélectionner un rôle par id
                    default_role_id = all_roles[0]["id"]
                    chosen_id = click.prompt(
                        "Sélectionner le role_id souhaité",
                        type=int,
                        default=default_role_id,
                        show_default=True,
                    )
                    role_row = next(
                        (r for r in all_roles if r["id"] == chosen_id), None
                    )
                    if not role_row:
                        console.print(f"[red]Rôle {chosen_id} introuvable.[/red]")
                        return

                    chosen_role_name = role_row["name"]

                    # 3) Créer l'utilisateur
                    console.print("[dim]Création de l'utilisateur...[/dim]")
                    new_user = users.create_user(
                        {
                            "username": username,
                            "email": email,
                            "employee_number": employee_number,
                            "password": password,  # hashé côté modèle/CRUD
                        }
                    )  # attendu: dict avec au moins 'id' et 'username'

                    # 4) Assigner le rôle choisi
                    console.print("[dim]Assignation du rôle...[/dim]")
                    users.add_role(new_user["id"], chosen_role_name)

                    console.print(
                        f"[green]Utilisateur créé : {new_user['username']} (id={new_user['id']})[/green]"
                    )
                    console.print(f"[green]Rôle assigné : {chosen_role_name}[/green]")

                except PermissionError as e:
                    console.print(f"[red]Permission refusée : {e}[/red]")
                except ValueError as e:
                    console.print(f"[red]Erreur : {e}[/red]")
                except Exception as e:
                    console.print(f"[red]Erreur inattendue : {e}[/red]")

        elif c == 2:
            rows = ctrl.list_users()
            rows = [_asdict_user(r) for r in rows]
            _print_table(
                "Utilisateurs",
                ["id", "username", "email", "employee_number", "roles", "created_at"],
                rows,
            )

        elif c == 3:
            user_id = click.prompt("ID utilisateur", type=int)
            email = _prompt_optional("Nouvel email")
            employee_number = _prompt_optional("Nouveau numéro d'employé")
            password = _prompt_optional("Nouveau mot de passe")
            roles = _prompt_optional("Nouveaux rôles (séparés par des virgules)")
            roles_list = [r.strip() for r in roles.split(",")] if roles else None

            msg = ctrl.update_user(
                user_id,
                email=email,
                employee_number=employee_number,
                password=password,
                roles=roles_list,
            )
            console.print(f"[green]{msg}[/green]")

        elif c == 4:
            user_id = click.prompt("ID utilisateur", type=int)
            confirm = click.confirm("Confirmer la suppression ?", default=False)
            if confirm:
                msg = ctrl.delete_user(user_id)
                console.print(f"[yellow]{msg}[/yellow]")

        elif c == 5:
            break
        else:
            console.print("[red]Choix invalide[/red]")


# ---------
# Helpers pour transformer tes objets en dicts (si tes controllers renvoient des modèles)
# Adapte selon tes attributs réels.
# ---------
def _asdict_client(o) -> dict:
    if isinstance(o, dict):
        return o
    return {
        "id": getattr(o, "id", ""),
        "name": getattr(o, "name", ""),
        "email": getattr(o, "email", ""),
        "phone": getattr(o, "phone", ""),
        "created_at": getattr(o, "created_at", ""),
    }


def _asdict_contract(o) -> dict:
    if isinstance(o, dict):
        return o
    return {
        "id": getattr(o, "id", ""),
        "client_id": getattr(o, "client_id", ""),
        "title": getattr(o, "title", ""),
        "amount": getattr(o, "amount", ""),
        "status": getattr(o, "status", ""),
        "created_at": getattr(o, "created_at", ""),
    }


def _asdict_event(o) -> dict:
    if isinstance(o, dict):
        return o
    return {
        "id": getattr(o, "id", ""),
        "contract_id": getattr(o, "contract_id", ""),
        "name": getattr(o, "name", ""),
        "date": getattr(o, "date", ""),
        "location": getattr(o, "location", ""),
        "note": getattr(o, "note", ""),
        "created_at": getattr(o, "created_at", ""),
    }


def _asdict_user(o) -> dict:
    if isinstance(o, dict):
        return o
    # suppose que o.roles est une liste de str ou objets avec .name
    roles_attr = getattr(o, "roles", [])
    if roles_attr and not isinstance(roles_attr, str):
        try:
            roles_attr = ", ".join([getattr(r, "name", str(r)) for r in roles_attr])
        except Exception:
            roles_attr = str(roles_attr)

    return {
        "id": getattr(o, "id", ""),
        "username": getattr(o, "username", ""),
        "email": getattr(o, "email", ""),
        "employee_number": getattr(o, "employee_number", ""),
        "roles": roles_attr,
        "created_at": getattr(o, "created_at", ""),
    }
