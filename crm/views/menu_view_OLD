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
from ..auth.permission import Permission
from ..auth.permission_config import Crud


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

    def _filter_items_by_permissions(
        self,
        user,
        items: list[tuple[str, Callable, list, str]],
    ) -> list[tuple[str, Callable]]:
        """
        Filtre les items de menu selon les permissions de l'utilisateur.
        - items: liste de (label, action, [Crud operations], resource)
        Retourne une liste réduite [(label, action), ...]
        """
        allowed = []
        for label, action, ops, resource in items:
            # Si l'utilisateur a au moins une des opérations autorisées
            if any(
                Permission.has_permission(user, resource=resource, op=op) for op in ops
            ):
                allowed.append((label, action))
        return allowed

    def run_menu(
        self,
        ctx: click.Context,
        title: str,
        items: list[tuple[str, Callable]],  # [(label, action), ...]
        logout: bool = False,
    ) -> None:
        """
        Affiche un menu et exécute les actions correspondantes.
        - items: liste de (label, action). La numérotation démarre à 1.
        - R: retour (break), 0: quitter (self.handle_quit()).
        """
        while True:
            self._clear_screen()
            self.console.print(f"\n[bold cyan]{title}[/bold cyan]")

            # affichage des entrées numérotées
            for i, (label, _) in enumerate(items, start=1):
                self.console.print(f"{i}. {label}")

            # lignes standardisées
            if not logout:
                self.console.print(
                    f"\n[bold yellow]R.[/bold yellow][yellow] Retour[/yellow]"
                )
            else:
                self.console.print(
                    f"\n[bold yellow]R.[/bold yellow][yellow] Se déconnecter[/yellow]"
                )
            self.print_quit_option()  # suppose qu'affiche "0. Quitter"

            # messages d'état
            self.app_state.display_error_or_success_message()

            # lecture choix
            raw = click.prompt("\nChoix", type=str).strip()
            choice = raw.upper()

            try:
                if choice == "0":
                    self.handle_quit()
                    return
                if choice in ("R", "BACK"):
                    if logout:
                        self.cli_utils.invoke(ctx, "logout")
                    break

                if choice.isdigit():
                    idx = int(choice)
                    if 1 <= idx <= len(items):
                        _, action = items[idx - 1]
                        action()
                    else:
                        self.app_state.set_error_message("[red]Choix invalide[/red]")
                else:
                    self.app_state.set_error_message("[red]Choix invalide[/red]")

            except Exception as e:
                self.app_state.set_error_message(str(e))

    def run(self, ctx: click.Context) -> None:
        raw_items = [
            (
                "Mon profil",
                lambda: self._menu_profile(ctx),
                [Crud.READ, Crud.READ_OWN],
                "user",
            ),
            ("Clients", lambda: self._menu_clients(ctx), [Crud.READ], "client"),
            ("Contrats", lambda: self._menu_contracts(ctx), [Crud.READ], "contract"),
            ("Événements", lambda: self._menu_events(ctx), [Crud.READ], "event"),
            (
                "Utilisateurs",
                lambda: self._menu_users(ctx),
                [Crud.READ],
                "user",
            ),
        ]

        user = self.user_ctrl._get_current_user()
        items = self._filter_items_by_permissions(user, raw_items)

        self.run_menu(ctx, "=== CRM - Menu principal ===", items, logout=True)

    def _menu_profile(self, ctx: click.Context) -> None:
        me = self.user_ctrl._get_current_user()
        raw_items = [
            (
                "Voir mon profil",
                lambda: self.cli_utils.invoke(ctx, "list-users", user_id=me.id),
                [Crud.READ, Crud.READ_OWN],
                "user",
            ),
            (
                "Changer mon mot de passe",
                lambda: self.cli_utils.invoke(
                    ctx, "update-user-password", user_id=me.id
                ),
                [Crud.UPDATE_OWN],
                "user",
            ),
        ]

        user = self.user_ctrl._get_current_user()
        items = self._filter_items_by_permissions(user, raw_items)

        self.run_menu(ctx, "-- Mon profil --", items, logout=False)

    def _menu_clients(self, ctx: click.Context) -> None:
        raw_items = [
            (
                "Créer un client",
                lambda: self.cli_utils.invoke(ctx, "create-client"),
                [Crud.CREATE],
                "client",
            ),
            (
                "Lister les clients",
                lambda: self.cli_utils.invoke(ctx, "list-clients"),
                [Crud.READ],
                "client",
            ),
            (
                "Modifier les infos d'un client",
                lambda: self.cli_utils.invoke(ctx, "update-client"),
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "client",
            ),
            (
                "Assigner/Changer le commercial",
                lambda: self.cli_utils.invoke(ctx, "update-sales-contact"),
                [Crud.ONLY_ADMIN],
                "client",
            ),
            (
                "Supprimer un client",
                lambda: self.cli_utils.invoke(ctx, "delete-client"),
                [Crud.ONLY_ADMIN],
                "client",
            ),
        ]

        user = self.user_ctrl._get_current_user()
        items = self._filter_items_by_permissions(user, raw_items)

        self.run_menu(ctx, "-- Clients --", items)

    def _menu_contracts(self, ctx: click.Context) -> None:
        raw_items = [
            (
                "Créer un contrat",
                lambda: self.cli_utils.invoke(ctx, "create-contract"),
                [Crud.CREATE],
                "contract",
            ),
            (
                "Lister les contrats",
                lambda: self.cli_utils.invoke(ctx, "list-contracts"),
                [Crud.READ],
                "contract",
            ),
            (
                "Signer un contrat",
                lambda: self.cli_utils.invoke(ctx, "sign-contract"),
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "contract",
            ),
            (
                "Enregistrer un paiement",
                lambda: self.cli_utils.invoke(ctx, "update-contract-amount"),
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "contract",
            ),
            (
                "Supprimer un contrat",
                lambda: self.cli_utils.invoke(ctx, "delete-contract"),
                [Crud.DELETE],
                "contract",
            ),
        ]

        user = self.user_ctrl._get_current_user()
        items = self._filter_items_by_permissions(user, raw_items)

        self.run_menu(ctx, "-- Contrats --", items)

    def _menu_events(self, ctx: click.Context) -> None:
        raw_items = [
            (
                "Créer un événement",
                lambda: self.cli_utils.invoke(ctx, "create-event"),
                [Crud.CREATE],
                "event",
            ),
            (
                "Lister les événements",
                lambda: self.cli_utils.invoke(ctx, "list-events"),
                [Crud.READ],
                "event",
            ),
            (
                "Modifier un événement",
                lambda: self.cli_utils.invoke(ctx, "update-event"),
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "event",
            ),
            (
                "Ajouter une note",
                lambda: self.cli_utils.invoke(ctx, "add-event-note"),
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "event",
            ),
            (
                "Retirer une note",
                lambda: self.cli_utils.invoke(ctx, "delete-note"),
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "event",
            ),
            (
                "Assigner le support",
                lambda: self.cli_utils.invoke(ctx, "update-support"),
                [Crud.UPDATE],
                "event",
            ),
            (
                "Supprimer un événement",
                lambda: self.cli_utils.invoke(ctx, "delete-event"),
                [Crud.DELETE],
                "event",
            ),
        ]

        user = self.user_ctrl._get_current_user()
        items = self._filter_items_by_permissions(user, raw_items)

        self.run_menu(ctx, "-- Evénements --", items)

    def _menu_users(self, ctx: click.Context) -> None:
        raw_items = [
            (
                "Créer un utilisateur",
                lambda: self.cli_utils.invoke(ctx, "create-user"),
                [Crud.CREATE],
                "user",
            ),
            (
                "Lister les utilisateurs",
                lambda: self.cli_utils.invoke(ctx, "list-users"),
                [Crud.READ],
                "user",
            ),
            (
                "Modifier un utilisateur",
                lambda: self.cli_utils.invoke(ctx, "update-user"),
                [Crud.UPDATE],
                "user",
            ),
            (
                "Supprimer un utilisateur",
                lambda: self.cli_utils.invoke(ctx, "delete-user"),
                [Crud.DELETE],
                "user",
            ),
        ]

        user = self.user_ctrl._get_current_user()
        items = self._filter_items_by_permissions(user, raw_items)

        self.run_menu(ctx, "-- Utilisateurs --", items)

    def modify_user_menu(self, user_id: int, username: str, ctx: click.Context) -> None:
        raw_items = [
            (
                "Modifier les informations",
                lambda: self.cli_utils.invoke(
                    ctx, "update-user-infos", user_id=user_id
                ),
                [Crud.UPDATE],
                "user",
            ),
            (
                "Modifier le mot de passe",
                lambda: self.cli_utils.invoke(
                    ctx, "update-user-password", user_id=user_id
                ),
                [Crud.ONLY_ADMIN],
                "user",
            ),
            (
                "Ajouter un rôle",
                lambda: self.cli_utils.invoke(ctx, "add-user-role", user_id=user_id),
                [Crud.CREATE],
                "user_role",
            ),
            (
                "Supprimer un rôle",
                lambda: self.cli_utils.invoke(ctx, "remove-user-role", user_id=user_id),
                [Crud.DELETE],
                "user_role",
            ),
        ]

        user = self.user_ctrl._get_current_user()
        items = self._filter_items_by_permissions(user, raw_items)

        self.run_menu(ctx, f"-- Modification de l'utilisateur : {username} --", items)


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
