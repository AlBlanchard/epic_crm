import sys
from .base import AbstractController
from rich.console import Console
from crm.utils.app_state import AppState

from ..menu_controllers.user_menu_controller import UserMenuController
from ..menu_controllers.client_menu_controller import ClientMenuController
from ..menu_controllers.contract_menu_controller import ContractMenuController
from ..menu_controllers.event_menu_controller import EventMenuController
from ..controllers.user_controller import UserController
from ..views.menu_view import MenuView
from ..auth.permission_config import Crud
from ..auth.permission import Permission
from ..controllers.auth_controller import AuthController


class MainController(AbstractController):
    def _setup_services(self):
        self.view = MenuView()
        self.user_menu_ctrl = UserMenuController()
        self.client_menu_ctrl = ClientMenuController()
        self.contract_menu_ctrl = ContractMenuController()
        self.event_menu_ctrl = EventMenuController()
        self.user_ctrl = UserController()
        self.auth_ctrl = AuthController()
        self.console = Console()
        self.app_state = AppState()
        self.auth_ctrl = AuthController()

    def _filter_items_by_permissions(self, user, raw_items):
        """Filtre les actions autorisées selon les permissions"""
        allowed = []
        for label, action, ops, resource in raw_items:
            if any(
                Permission.has_permission(user, resource=resource, op=op) for op in ops
            ):
                allowed.append((label, action))
        return allowed

    def _run_generic_menu(self, title: str, raw_items: list[tuple], logout=False):
        """
        Fonction générique qui :
        - filtre par permission
        - affiche le menu
        - exécute l'action choisie
        """
        # Chaque sous menu est autonome, permet de rester dans la boucle à chaque retour
        while True:
            user = self.user_menu_ctrl._get_current_user()
            allowed = self._filter_items_by_permissions(user, raw_items)

            # Récupération des labels (noms des actions)
            labels = [label for label, _ in allowed]
            choice = self.view.run_menu(title=title, items=labels, logout=logout)

            if choice == "0":
                sys.exit(0)

            if choice == "R":
                if logout:
                    self.auth_ctrl.logout()
                break

            # Sélectionne l'action en fonction du choix retourné
            if isinstance(choice, int):
                idx = int(choice) - 1
                if 0 <= idx < len(allowed):
                    _, action = allowed[idx]
                    action()

    def run(self):
        # Vérif auth
        if not self.auth_ctrl.me_safe():
            self.console.print("[bold yellow]Connexion requise.[/bold yellow]")
            self.auth_ctrl.login_interactive()

        self.show_main_menu()

    def show_main_menu(self):
        """Menu principal"""
        raw_items = [
            ("Mon profil", self.show_menu_my_profile, [Crud.READ_OWN], "user"),
            ("Clients", self.show_menu_clients, [Crud.READ], "client"),
            ("Contrats", self.show_menu_contracts, [Crud.READ], "contract"),
            ("Événements", self.show_menu_events, [Crud.READ], "event"),
            ("Utilisateurs", self.show_menu_users, [Crud.READ], "user"),
        ]

        self._run_generic_menu("=== CRM - Menu principal ===", raw_items, logout=True)

    def show_menu_my_profile(self):
        me = self.user_menu_ctrl._get_current_user()
        raw_items = [
            (
                "Voir mon profil",
                lambda: self.user_menu_ctrl.show_user_list(user_id=me.id),
                [Crud.READ, Crud.READ_OWN],
                "user",
            ),
            (
                "Changer mon mot de passe",
                lambda: self.user_menu_ctrl.show_update_password(user_id=me.id),
                [Crud.UPDATE_OWN],
                "user",
            ),
        ]

        self._run_generic_menu("-- Mon profil --", raw_items)

    def show_menu_clients(self):
        raw_items = [
            (
                "Créer un client",
                self.client_menu_ctrl.show_create_client,
                [Crud.CREATE],
                "client",
            ),
            (
                "Lister les clients",
                self.client_menu_ctrl.show_list_clients,
                [Crud.READ],
                "client",
            ),
            (
                "Modifier les infos d'un client",
                self.client_menu_ctrl.show_update_client,
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "client",
            ),
            (
                "Assigner/Changer le commercial",
                self.client_menu_ctrl.show_update_sales_contact,
                [Crud.ONLY_ADMIN],
                "client",
            ),
            (
                "Supprimer un client",
                self.client_menu_ctrl.show_delete_client,
                [Crud.ONLY_ADMIN],
                "client",
            ),
        ]

        self._run_generic_menu("-- Clients --", raw_items)

    def show_menu_contracts(self):
        raw_items = [
            (
                "Créer un contrat",
                self.contract_menu_ctrl.show_create_contract,
                [Crud.CREATE],
                "contract",
            ),
            (
                "Lister les contrats",
                self.contract_menu_ctrl.show_list_contracts,
                [Crud.READ],
                "contract",
            ),
            (
                "Signer un contrat",
                self.contract_menu_ctrl.show_sign_contract,
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "contract",
            ),
            (
                "Enregistrer un paiement",
                self.contract_menu_ctrl.show_update_contract_amount,
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "contract",
            ),
            (
                "Supprimer un contrat",
                self.contract_menu_ctrl.show_delete_contract,
                [Crud.DELETE],
                "contract",
            ),
        ]

        self._run_generic_menu("-- Contrats --", raw_items)

    def show_menu_events(self):
        raw_items = [
            (
                "Créer un événement",
                self.event_menu_ctrl.show_create_event,
                [Crud.CREATE],
                "event",
            ),
            (
                "Lister les événements",
                self.event_menu_ctrl.show_list_events,
                [Crud.READ],
                "event",
            ),
            (
                "Modifier un événement",
                self.event_menu_ctrl.show_update_event,
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "event",
            ),
            (
                "Ajouter une note",
                self.event_menu_ctrl.show_add_event_note,
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "event",
            ),
            (
                "Retirer une note",
                self.event_menu_ctrl.show_delete_note,
                [Crud.UPDATE, Crud.UPDATE_OWN],
                "event",
            ),
            (
                "Assigner le support",
                self.event_menu_ctrl.show_update_support,
                [Crud.UPDATE],
                "event",
            ),
            (
                "Supprimer un événement",
                self.event_menu_ctrl.show_delete_event,
                [Crud.DELETE],
                "event",
            ),
        ]

        self._run_generic_menu("-- Evénements --", raw_items)

    def show_menu_users(self):
        raw_items = [
            (
                "Créer un utilisateur",
                self.user_menu_ctrl.show_create_user,
                [Crud.CREATE],
                "user",
            ),
            (
                "Lister les utilisateurs",
                self.user_menu_ctrl.show_user_list,
                [Crud.READ],
                "user",
            ),
            (
                "Modifier un utilisateur",
                # En lambda pour éviter que la fonction ne se lance d'office
                lambda: (user_id := self.user_menu_ctrl.show_user_list(selector=True))
                and self.show_menu_modify_user(user_id),
                [Crud.UPDATE],
                "user",
            ),
            (
                "Supprimer un utilisateur",
                self.user_menu_ctrl.show_delete_user,
                [Crud.DELETE],
                "user",
            ),
        ]

        self._run_generic_menu("-- Utilisateurs --", raw_items)

    def show_menu_modify_user(self, user_id: int):
        raw_items = [
            (
                "Modifier les informations",
                lambda: self.user_menu_ctrl.show_update_user_infos(user_id),
                [Crud.UPDATE],
                "user",
            ),
            (
                "Modifier le mot de passe",
                lambda: self.user_menu_ctrl.show_update_password(user_id),
                [Crud.ONLY_ADMIN],
                "user",
            ),
            (
                "Ajouter un rôle",
                lambda: self.user_menu_ctrl.show_add_user_role(user_id),
                [Crud.CREATE],
                "user_role",
            ),
            (
                "Supprimer un rôle",
                lambda: self.user_menu_ctrl.show_remove_user_role(user_id),
                [Crud.DELETE],
                "user_role",
            ),
        ]

        user_name = self.user_ctrl.get_user_name(user_id)

        self._run_generic_menu(f"-- Modifier l'utilisateur : {user_name} --", raw_items)
