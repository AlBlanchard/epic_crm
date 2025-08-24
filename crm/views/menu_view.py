# views/menu_view.py
import click
from typing import Optional, Callable
from rich.console import Console
from .auth_view import AuthView
from .view import BaseView
from ..controllers.client_controller import ClientController
from ..controllers.contract_controller import ContractController
from ..controllers.event_controller import EventController
from ..controllers.user_controller import UserController
from ..utils.app_state import AppState
from ..utils.cli_utils import CliUtils


class MenuView(BaseView):
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
        super().__init__(console=console)
        self.auth_view = auth_view or AuthView()
        self.client_ctrl = client_ctrl or ClientController()
        self.contract_ctrl = contract_ctrl or ContractController()
        self.event_ctrl = event_ctrl or EventController()
        self.user_ctrl = user_ctrl or UserController()

    def _setup_services(self) -> None:
        self.auth_view = AuthView()
        self.client_ctrl = ClientController()
        self.contract_ctrl = ContractController()
        self.event_ctrl = EventController()
        self.user_ctrl = UserController()
        self.app_state = AppState()
        self.cli_utils = CliUtils()

    def run_menu(
        self,
        ctx: click.Context,
        title: str,
        items: list[tuple[str, Callable]],  # [(label, action), ...]
    ) -> None:
        """
        Affiche un menu et exécute les actions correspondantes.
        - items: liste de (label, action). La numérotation démarre à 1.
        - R: retour (break), 0: quitter (self.handle_quit()).
        """
        while True:
            self._clear_screen()
            self.console.print(f"\n[bold cyan]— {title} —[/bold cyan]")

            # affichage des entrées numérotées
            for i, (label, _) in enumerate(items, start=1):
                self.console.print(f"{i}. {label}")

            # lignes standardisées
            self.console.print(
                f"{len(items)+1}. [yellow]Retour[/yellow]  ([bold]R[/bold])"
            )
            self.print_quit_option()  # suppose qu'affiche "0. Quitter"

            # messages d'état
            self.app_state.display_error_or_success_message()

            # lecture choix
            raw = click.prompt(
                "Ton choix (chiffre, R pour retour, 0 pour quitter)", type=str
            ).strip()
            choice = raw.upper()

            try:
                if choice == "0":
                    self.handle_quit()
                    return
                if choice in ("R", "BACK"):
                    break

                if choice.isdigit():
                    idx = int(choice)
                    if 1 <= idx <= len(items):
                        _, action = items[idx - 1]
                        action()  # exécute l’action
                    elif idx == len(items) + 1:
                        break
                    else:
                        self.console.print("[red]Choix invalide[/red]")
                else:
                    self.console.print("[red]Choix invalide[/red]")

            except Exception as e:
                # Centralise l’erreur pour un affichage uniformisé
                self.app_state.set_error_message(str(e))

    def run(self, ctx: click.Context) -> None:
        while True:
            self._clear_screen()

            self.console.print("\n[bold cyan]=== CRM — Menu principal ===[/bold cyan]")
            self.console.print("1. Clients")
            self.console.print("2. Contrats")
            self.console.print("3. Événements")
            self.console.print("4. Utilisateurs")
            self.console.print("5.[yellow] Se déconnecter [/yellow]")
            self.print_quit_option()

            self.app_state.display_error_or_success_message()

            choice = self.ask_choice()

            try:
                if choice == 0:
                    self.handle_quit()
                if choice == 1:
                    self._menu_clients(ctx)
                elif choice == 2:
                    self._menu_contracts(ctx)
                elif choice == 3:
                    self._menu_events(ctx)
                elif choice == 4:
                    self._menu_users(ctx)
                elif choice == 5:
                    self.cli_utils.invoke(ctx, "logout")
                    break
                else:
                    self.app_state.set_error_message("Choix invalide")
                    self.app_state.testprint()

            except Exception as e:
                self.app_state.set_error_message(str(e))

    def _menu_clients(self, ctx: click.Context) -> None:
        while True:
            self._clear_screen()
            self.console.print("\n[bold cyan]— Clients —[/bold cyan]")
            self.console.print("1. Créer un client")
            self.console.print("2. Lister les clients")
            self.console.print("3. Modifier un client")
            self.console.print("4. Supprimer un client")
            self.console.print("5. [yellow]Retour[/yellow]")
            self.print_quit_option()

            self.app_state.display_error_or_success_message()

            choice = self.ask_choice()

            try:
                if choice == 0:
                    self.handle_quit()
                elif choice == 1:
                    self.cli_utils.invoke(ctx, "create-client")
                elif choice == 2:
                    self.cli_utils.invoke(ctx, "list-clients")
                elif choice == 3:
                    self.cli_utils.invoke(ctx, "update-client")
                elif choice == 4:
                    self.cli_utils.invoke(ctx, "delete-client")
                elif choice == 5:
                    break
                else:
                    self.console.print("[red]Choix invalide[/red]")
            except Exception as e:
                self.app_state.set_error_message(str(e))

    def _menu_contracts(self, ctx: click.Context) -> None:
        while True:
            self._clear_screen()
            self.console.print("\n[bold cyan]— Contrats —[/bold cyan]")
            self.console.print("1. Créer un contrat")
            self.console.print("2. Lister les contrats")
            self.console.print("3. Signer un contrat")
            self.console.print("4. Enregistrer un paiement")
            self.console.print("5. Supprimer un contrat")
            self.console.print("6. [yellow]Retour[/yellow]")
            self.print_quit_option()

            self.app_state.display_error_or_success_message()
            choice = self.ask_choice()

            try:
                if choice == 0:
                    self.handle_quit()
                elif choice == 1:
                    self.cli_utils.invoke(ctx, "create-contract")
                elif choice == 2:
                    self.cli_utils.invoke(ctx, "list-contracts")
                elif choice == 3:
                    self.cli_utils.invoke(ctx, "sign-contract")
                elif choice == 4:
                    self.cli_utils.invoke(ctx, "update-contract-amount")
                elif choice == 5:
                    self.cli_utils.invoke(ctx, "delete-contract")
                elif choice == 6:
                    break
                else:
                    self.console.print("[red]Choix invalide[/red]")
            except Exception as e:
                self.app_state.set_error_message(str(e))

    def _menu_events(self, ctx: click.Context) -> None:
        while True:
            self._clear_screen()
            self.console.print("\n[bold cyan]— Evénements —[/bold cyan]")
            self.console.print("1. Créer un événement")
            self.console.print("2. Lister les événements")
            self.console.print("3. Modifier un événement")
            self.console.print("4. Ajouter une note")
            self.console.print("5. Retirer une note")
            self.console.print("6. Assigner le support")
            self.console.print("7. Supprimer un événement")
            self.console.print("8. [yellow]Retour[/yellow]")
            self.print_quit_option()

            self.app_state.display_error_or_success_message()
            choice = self.ask_choice()

            try:
                if choice == 0:
                    self.handle_quit()
                elif choice == 1:
                    self.cli_utils.invoke(ctx, "create-event")
                elif choice == 2:
                    self.cli_utils.invoke(ctx, "list-events")
                elif choice == 3:
                    self.cli_utils.invoke(ctx, "update-event")
                elif choice == 4:
                    self.cli_utils.invoke(ctx, "add-event-note")
                elif choice == 5:
                    self.cli_utils.invoke(ctx, "delete-note")
                elif choice == 6:
                    self.cli_utils.invoke(ctx, "update-support")
                elif choice == 7:
                    self.cli_utils.invoke(ctx, "delete-event")
                elif choice == 8:
                    break
                else:
                    self.console.print("[red]Choix invalide[/red]")
            except Exception as e:
                self.app_state.set_error_message(str(e))

    def _menu_users(self, ctx: click.Context) -> None:
        while True:
            self._clear_screen()
            self.console.print("\n[bold cyan]— Utilisateurs —[/bold cyan]")
            self.console.print("1. Créer un utilisateur")
            self.console.print("2. Lister les utilisateurs")
            self.console.print("3. Modifier un utilisateur")
            self.console.print("4. Supprimer un utilisateur")
            self.console.print("5. Retour")
            self.print_quit_option()

            self.app_state.display_error_or_success_message()
            choice = self.ask_choice()

            try:
                if choice == 0:
                    self.handle_quit()
                elif choice == 1:
                    self.cli_utils.invoke(ctx, "create-user")
                elif choice == 2:
                    self.cli_utils.invoke(ctx, "list-users")
                elif choice == 3:
                    self.cli_utils.invoke(ctx, "update-user")
                elif choice == 4:
                    self.cli_utils.invoke(ctx, "delete-user")
                elif choice == 5:
                    break
                else:
                    self.console.print("[red]Choix invalide[/red]")
            except Exception as e:
                self.app_state.set_error_message(str(e))

    def modify_user_menu(self, user_id: int, username: str, ctx: click.Context) -> None:
        while True:
            self._clear_screen()
            self.console.print(
                f"\n[bold yellow]-- Modification de l'utilisateur : '{username}' --[/bold yellow]"
            )
            self.console.print("1. Modifier les informations")
            self.console.print("2. Modifier le mot de passe")
            self.console.print("3. Ajouter un rôle")
            self.console.print("4. Supprimer un rôle")
            self.console.print("5. Retour")
            self.print_quit_option()

            self.app_state.display_error_or_success_message()
            choice = self.ask_choice()

            try:
                if choice == 0:
                    self.handle_quit()
                elif choice == 1:
                    self.cli_utils.invoke(ctx, "update-user-infos", user_id=user_id)
                    break
                elif choice == 2:
                    self.cli_utils.invoke(ctx, "update-user-password", user_id=user_id)
                    break
                elif choice == 3:
                    self.cli_utils.invoke(ctx, "add-user-role", user_id=user_id)
                    break
                elif choice == 4:
                    self.cli_utils.invoke(ctx, "remove-user-role", user_id=user_id)
                    break
                elif choice == 5:
                    break
                else:
                    self.app_state.set_error_message("Choix invalide")
                    self.app_state.testprint()

            except Exception as e:
                self.app_state.set_error_message(str(e))


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
