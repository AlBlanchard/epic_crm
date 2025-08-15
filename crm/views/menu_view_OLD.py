import click
from typing import Any, Dict, Iterable, List, Optional

from rich.console import Console
from rich.table import Table

from ..database import SessionLocal
from .auth_view import AuthView
from ..controllers.client_controller import ClientController
from ..controllers.contract_controller import ContractController
from ..controllers.event_controller import EventController
from ..controllers.user_controller import UserController
from ..controllers.role_controller import RoleController


class MenuView:
    """
    Vue principale (CLI) du CRM.
    - Entièrement côté View : saisies, affichage, navigation.
    - Toute la validation métier et les erreurs détaillées restent côté Controller.
    """

    def __init__(
        self,
        *,
        console: Optional[Console] = None,
        auth_view: Optional[AuthView] = None,
        client_ctrl: Optional[ClientController] = None,
        contract_ctrl: Optional[ContractController] = None,
        event_ctrl: Optional[EventController] = None,
        user_ctrl: Optional[UserController] = None,
    ) -> None:
        self.console = console or Console()
        self.auth_view = auth_view or AuthView()
        # Les controllers peuvent être injectés (tests) ou instanciés ici
        self.client_ctrl = client_ctrl or ClientController()
        self.contract_ctrl = contract_ctrl or ContractController()
        self.event_ctrl = event_ctrl or EventController()
        self.user_ctrl = user_ctrl or UserController()

    # ----------------------
    # Helpers (View-level)
    # ----------------------
    @staticmethod
    def _prompt_optional_int(label: str) -> Optional[int]:
        val = click.prompt(label, default="", show_default=False).strip()
        if not val:
            return None
        try:
            return int(val)
        except ValueError:
            Console().print(
                "[red]Veuillez entrer un entier valide ou laisser vide.[/red]"
            )
            return MenuView._prompt_optional_int(label)

    @staticmethod
    def _prompt_non_empty(label: str) -> str:
        """Validation minimale côté View : non vide. Le reste => Controller."""
        while True:
            val = click.prompt(label).strip()
            if val:
                return val
            Console().print("[red]Ce champ est requis.[/red]")

    @staticmethod
    def _prompt_optional(label: str) -> Optional[str]:
        val = click.prompt(label, default="", show_default=False).strip()
        return val or None

    def _print_table(
        self, title: str, columns: List[str], rows: List[Dict[str, Any]]
    ) -> None:
        table = Table(title=title)
        for col in columns:
            table.add_column(col, overflow="fold")
        for r in rows:
            table.add_row(*[str(r.get(c, "")) for c in columns])
        self.console.print(table)

    # ---------
    # Helpers pour transformer d'éventuels modèles en dicts
    # (si tes controllers renvoient des objets ORM).
    # Adapte selon tes attributs réels.
    # ---------
    @staticmethod
    def _asdict_client(o: Any) -> Dict[str, Any]:
        if isinstance(o, dict):
            return o
        return {
            "id": getattr(o, "id", ""),
            "name": getattr(o, "name", ""),
            "email": getattr(o, "email", ""),
            "phone": getattr(o, "phone", ""),
            "created_at": getattr(o, "created_at", ""),
        }

    @staticmethod
    def _asdict_contract(o: Any) -> Dict[str, Any]:
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

    @staticmethod
    def _asdict_event(o: Any) -> Dict[str, Any]:
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

    @staticmethod
    def _asdict_user(o: Any) -> Dict[str, Any]:
        if isinstance(o, dict):
            return o
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

    # ----------------------
    # Menus
    # ----------------------
    def run(self, ctx: click.Context) -> None:
        """Boucle du menu principal."""
        while True:
            self.console.print("\n[bold cyan]=== CRM — Menu principal ===[/bold cyan]")
            self.console.print("1. Clients")
            self.console.print("2. Contrats")
            self.console.print("3. Événements")
            self.console.print("4. Utilisateurs")
            self.console.print("5. Se déconnecter")
            self.console.print("6. Quitter")

            choice = click.prompt("Choix", type=int)

            try:
                if choice == 1:
                    self._menu_clients()
                elif choice == 2:
                    self._menu_contracts()
                elif choice == 3:
                    self._menu_events()
                elif choice == 4:
                    self._menu_users()
                elif choice == 5:
                    # Déconnexion locale (supprime le fichier de tokens)
                    ctx.invoke(self.auth_view.logout_cmd)
                    break
                elif choice == 6:
                    self.console.print("👋 À bientôt.")
                    break
                else:
                    self.console.print("[red]Choix invalide[/red]")
            except Exception as e:
                # Catch-all View : le détail de validation reste côté Controller
                self.console.print(f"[red]Erreur : {e}[/red]")

    # ----------------------
    # Sous-menus (Clients)
    # ----------------------
    def _menu_clients(self) -> None:
        while True:
            self.console.print("\n[bold]— Clients —[/bold]")
            self.console.print("1. Créer un client")
            self.console.print("2. Lister les clients")
            self.console.print("3. Modifier un client")
            self.console.print("4. Supprimer un client")
            self.console.print("5. Retour")

            c = click.prompt("Choix", type=int)
            if c == 1:
                name = self._prompt_non_empty("Nom")
                email = self._prompt_non_empty("Email")
                phone = self._prompt_optional("Téléphone")
                msg = self.client_ctrl.create_client(
                    name=name, email=email, phone=phone
                )
                self.console.print(f"[green]{msg}[/green]")

            elif c == 2:
                rows = self.client_ctrl.list_clients()
                rows = [self._asdict_client(r) for r in rows]
                self._print_table(
                    "Clients", ["id", "name", "email", "phone", "created_at"], rows
                )

            elif c == 3:
                client_id = click.prompt("ID du client", type=int)
                name = self._prompt_optional(
                    "Nouveau nom (laisser vide pour ne pas changer)"
                )
                email = self._prompt_optional(
                    "Nouvel email (laisser vide pour ne pas changer)"
                )
                phone = self._prompt_optional(
                    "Nouveau téléphone (laisser vide pour ne pas changer)"
                )
                msg = self.client_ctrl.update_client(
                    client_id, name=name, email=email, phone=phone
                )
                self.console.print(f"[green]{msg}[/green]")

            elif c == 4:
                client_id = click.prompt("ID du client", type=int)
                confirm = click.confirm("Confirmer la suppression ?", default=False)
                if confirm:
                    msg = self.client_ctrl.delete_client(client_id)
                    self.console.print(f"[yellow]{msg}[/yellow]")

            elif c == 5:
                break
            else:
                self.console.print("[red]Choix invalide[/red]")

    # ----------------------
    # Sous-menus (Contrats)
    # ----------------------
    def _menu_contracts(self) -> None:
        while True:
            self.console.print("\n[bold]— Contrats —[/bold]")
            self.console.print("1. Créer un contrat")
            self.console.print("2. Lister les contrats")
            self.console.print("3. Modifier un contrat")
            self.console.print("4. Supprimer un contrat")
            self.console.print("5. Retour")

            c = click.prompt("Choix", type=int)
            if c == 1:
                client_id = click.prompt("ID client", type=int)
                title = self._prompt_non_empty("Titre du contrat")
                amount = click.prompt("Montant (€)", type=float)
                status = self._prompt_optional("Statut (draft/active/closed)")
                msg = self.contract_ctrl.create_contract(
                    client_id=client_id, title=title, amount=amount, status=status
                )
                self.console.print(f"[green]{msg}[/green]")

            elif c == 2:
                rows = self.contract_ctrl.list_contracts()
                rows = [self._asdict_contract(r) for r in rows]
                self._print_table(
                    "Contrats",
                    ["id", "client_id", "title", "amount", "status", "created_at"],
                    rows,
                )

            elif c == 3:
                contract_id = click.prompt("ID du contrat", type=int)
                title = self._prompt_optional("Nouveau titre")
                amount = self._prompt_optional("Nouveau montant (€)")
                status = self._prompt_optional("Nouveau statut (draft/active/closed)")
                amount_val = float(amount) if amount is not None else None
                msg = self.contract_ctrl.update_contract(
                    contract_id, title=title, amount=amount_val, status=status
                )
                self.console.print(f"[green]{msg}[/green]")

            elif c == 4:
                contract_id = click.prompt("ID du contrat", type=int)
                confirm = click.confirm("Confirmer la suppression ?", default=False)
                if confirm:
                    msg = self.contract_ctrl.delete_contract(contract_id)
                    self.console.print(f"[yellow]{msg}[/yellow]")

            elif c == 5:
                break
            else:
                self.console.print("[red]Choix invalide[/red]")

    # ----------------------
    # Sous-menus (Événements)
    # ----------------------
    def _menu_events(self) -> None:
        while True:
            self.console.print("\n[bold]— Événements —[/bold]")
            self.console.print("1. Créer un événement")
            self.console.print("2. Lister les événements")
            self.console.print("3. Modifier un événement")
            self.console.print("4. Supprimer un événement")
            self.console.print("5. Retour")

            c = click.prompt("Choix", type=int)
            if c == 1:
                contract_id = click.prompt("ID contrat", type=int)
                name = self._prompt_non_empty("Nom de l'événement")
                date_str = self._prompt_non_empty("Date (YYYY-MM-DD HH:MM)")
                location = self._prompt_optional("Lieu")
                note = self._prompt_optional("Note")
                msg = self.event_ctrl.create_event(
                    contract_id=contract_id,
                    name=name,
                    date_str=date_str,
                    location=location,
                    note=note,
                )
                self.console.print(f"[green]{msg}[/green]")

            elif c == 2:
                rows = self.event_ctrl.list_events()
                rows = [self._asdict_event(r) for r in rows]
                self._print_table(
                    "Événements",
                    [
                        "id",
                        "contract_id",
                        "name",
                        "date",
                        "location",
                        "note",
                        "created_at",
                    ],
                    rows,
                )

            elif c == 3:
                event_id = click.prompt("ID de l'événement", type=int)
                name = self._prompt_optional("Nouveau nom")
                date_str = self._prompt_optional("Nouvelle date (YYYY-MM-DD HH:MM)")
                location = self._prompt_optional("Nouveau lieu")
                note = self._prompt_optional("Nouvelle note")
                msg = self.event_ctrl.update_event(
                    event_id, name=name, date_str=date_str, location=location, note=note
                )
                self.console.print(f"[green]{msg}[/green]")

            elif c == 4:
                event_id = click.prompt("ID de l'événement", type=int)
                confirm = click.confirm("Confirmer la suppression ?", default=False)
                if confirm:
                    msg = self.event_ctrl.delete_event(event_id)
                    self.console.print(f"[yellow]{msg}[/yellow]")

            elif c == 5:
                break
            else:
                self.console.print("[red]Choix invalide[/red]")

    # ----------------------
    # Sous-menus (Utilisateurs)
    # ----------------------
    def _menu_users(self) -> None:
        while True:
            self.console.print("\n[bold]— Utilisateurs —[/bold]")
            self.console.print("1. Créer un utilisateur")
            self.console.print("2. Lister les utilisateurs")
            self.console.print("3. Modifier un utilisateur")
            self.console.print("4. Supprimer un utilisateur")
            self.console.print("5. Retour")

            c = click.prompt("Choix", type=int)
            if c == 1:
                # Création d'utilisateur + sélection d'un rôle existant
                username = self._prompt_non_empty("Nom d'utilisateur")
                email = self._prompt_non_empty("Email")
                employee_number = self._prompt_optional_int("Numéro d'employé")
                password = click.prompt("Mot de passe", hide_input=True)

                # Session locale uniquement pour la création + assignation de rôle
                with SessionLocal() as session:
                    users = UserController(session=session)
                    roles = RoleController(session=session)

                    try:
                        all_roles = (
                            roles.list_roles()
                        )  # attendu: list[dict] {'id','name',...}
                        if not all_roles:
                            self.console.print(
                                "[yellow]Aucun rôle n'existe encore. Créez-en d'abord (admin).[/yellow]"
                            )
                            return

                        self.console.print("\n[bold]Rôles disponibles :[/bold]")
                        for r in all_roles:
                            self.console.print(f"- {r['id']} : {r['name']}")

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
                            self.console.print(
                                f"[red]Rôle {chosen_id} introuvable.[/red]"
                            )
                            return

                        chosen_role_name = role_row["name"]

                        self.console.print("[dim]Création de l'utilisateur...[/dim]")
                        new_user = users.create_user(
                            {
                                "username": username,
                                "email": email,
                                "employee_number": employee_number,
                                "password": password,  # hash côté modèle/CRUD
                            }
                        )

                        self.console.print("[dim]Assignation du rôle...[/dim]")
                        users.add_role(new_user["id"], chosen_role_name)

                        self.console.print(
                            f"[green]Utilisateur créé : {new_user['username']} (id={new_user['id']})[/green]"
                        )
                        self.console.print(
                            f"[green]Rôle assigné : {chosen_role_name}[/green]"
                        )

                    except PermissionError as e:
                        self.console.print(f"[red]Permission refusée : {e}[/red]")
                    except ValueError as e:
                        self.console.print(f"[red]Erreur : {e}[/red]")
                    except Exception as e:
                        self.console.print(f"[red]Erreur inattendue : {e}[/red]")

            elif c == 2:
                rows = self.user_ctrl.list_users()
                rows = [self._asdict_user(r) for r in rows]
                self._print_table(
                    "Utilisateurs",
                    [
                        "id",
                        "username",
                        "email",
                        "employee_number",
                        "roles",
                        "created_at",
                    ],
                    rows,
                )

            elif c == 3:
                user_id = click.prompt("ID utilisateur", type=int)
                email = self._prompt_optional("Nouvel email")
                employee_number = self._prompt_optional("Nouveau numéro d'employé")
                password = self._prompt_optional("Nouveau mot de passe")
                roles = self._prompt_optional(
                    "Nouveaux rôles (séparés par des virgules)"
                )
                roles_list = [r.strip() for r in roles.split(",")] if roles else None

                msg = self.user_ctrl.update_user(
                    user_id,
                    email=email,
                    employee_number=employee_number,
                    password=password,
                    roles=roles_list,
                )
                self.console.print(f"[green]{msg}[/green]")

            elif c == 4:
                user_id = click.prompt("ID utilisateur", type=int)
                confirm = click.confirm("Confirmer la suppression ?", default=False)
                if confirm:
                    msg = self.user_ctrl.delete_user(user_id)
                    self.console.print(f"[yellow]{msg}[/yellow]")

            elif c == 5:
                break
            else:
                self.console.print("[red]Choix invalide[/red]")


# ----------------------
# Entrée CLI
# ----------------------
@click.command(name="menu")
@click.pass_context
def menu_cmd(ctx: click.Context) -> None:
    """
    Commande CLI : lance le menu principal du CRM via la MenuView (MVC).
    """
    view = MenuView()
    view.run(ctx)
