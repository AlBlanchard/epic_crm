# views/menu_view.py
import click
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table

from ..database import SessionLocal
from .auth_view import AuthView
from .view import BaseView
from ..controllers.client_controller import ClientController
from ..controllers.contract_controller import ContractController
from ..controllers.event_controller import EventController
from ..controllers.user_controller import UserController
from ..controllers.role_controller import RoleController
from ..utils.app_state import AppState


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
                    self._menu_clients()
                elif choice == 2:
                    self._menu_contracts()
                elif choice == 3:
                    self._menu_events()
                elif choice == 4:
                    self._menu_users()
                elif choice == 5:
                    ctx.invoke(self.auth_view.logout_cmd)
                    break
                else:
                    self.app_state.set_error_message("Choix invalide")
                    self.app_state.testprint()

            except Exception as e:
                self.app_state.set_error_message(str(e))

    def _menu_clients(self) -> None:
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
                    self.clients_view.create_client()
                elif choice == 2:
                    self.clients_view.list_clients()
                elif choice == 3:
                    self.clients_view.update_client()
                elif choice == 4:
                    self.clients_view.delete_client()
                elif choice == 5:
                    break
                else:
                    self.console.print("[red]Choix invalide[/red]")
            except Exception as e:
                self.app_state.set_error_message(str(e))

    def _menu_contracts(self) -> None:
        while True:
            self._clear_screen()
            self.console.print("\n[bold cyan]— Contrats —[/bold cyan]")
            self.console.print("1. Créer un contrat")
            self.console.print("2. Lister les contrats")
            self.console.print("3. Modifier un contrat")
            self.console.print("4. Supprimer un contrat")
            self.console.print("5. [yellow]Retour[/yellow]")
            self.print_quit_option()

            self.app_state.display_error_or_success_message()
            choice = self.ask_choice()

            try:
                if choice == 0:
                    self.handle_quit()
                elif choice == 1:
                    self.contracts_view.create_contract()
                elif choice == 2:
                    self.contracts_view.list_contracts()
                elif choice == 3:
                    self.contracts_view.update_contract()
                elif choice == 4:
                    self.contracts_view.delete_contract()
                elif choice == 5:
                    break
                else:
                    self.console.print("[red]Choix invalide[/red]")
            except Exception as e:
                self.app_state.set_error_message(str(e))

    def _menu_events(self) -> None:
        while True:
            self._clear_screen()
            self.console.print("\n[bold cyan]— Evénements —[/bold cyan]")
            self.console.print("1. Créer un événement")
            self.console.print("2. Lister les événements")
            self.console.print("3. Modifier un événement")
            self.console.print("4. Supprimer un événement")
            self.console.print("5. [yellow]Retour[/yellow]")
            self.print_quit_option()

            self.app_state.display_error_or_success_message()
            choice = self.ask_choice()

            try:
                if choice == 0:
                    self.handle_quit()
                elif choice == 1:
                    self.events_view.create_event()
                elif choice == 2:
                    self.events_view.list_events()
                elif choice == 3:
                    self.events_view.update_event()
                elif choice == 4:
                    self.events_view.delete_event()
                elif choice == 5:
                    break
                else:
                    self.console.print("[red]Choix invalide[/red]")
            except Exception as e:
                self.app_state.set_error_message(str(e))

    def _menu_users(self) -> None:
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
                    self.users_view.create_user()
                elif choice == 2:
                    self.users_view.list_users()
                elif choice == 3:
                    self.users_view.update_user()
                elif choice == 4:
                    self.users_view.delete_user()
                elif choice == 5:
                    break
                else:
                    self.console.print("[red]Choix invalide[/red]")
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
