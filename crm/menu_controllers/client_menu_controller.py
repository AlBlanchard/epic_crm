from ..controllers.base import AbstractController
from ..auth.permission import Permission
from ..views.client_view import ClientView
from ..views.user_view import UserView
from ..controllers.client_controller import ClientController
from ..controllers.user_controller import UserController
from ..auth.permission_config import ROLE_ADMIN, ROLE_SALES
from ..controllers.filter_controller import FilterController
from ..utils.validations import Validations

class ClientMenuController(AbstractController):

    def _setup_services(self):
        self.view = ClientView()
        self.user_view = UserView()
        self.user_ctrl = UserController()
        self.client_ctrl = ClientController()
        self.filter_ctrl = FilterController()


    def show_create_client(self) -> None:
        try:
        # Il y a une vérif dans le ctrl mais on la refait ici sinon ça lance les prompts
            me = self._get_current_user()
            if not Permission.create_permission(me, "client"):
                raise PermissionError("Accès refusé.")

            result = self.view.create_client_flow(sales_contact_id=me.id)
            if result is None:
                return

            self.client_ctrl.create_client(result)
            self.view.app_state.set_success_message("Le client a été créé avec succès.")
        except Exception as e:
            if self.view.app_state:
                self.view.app_state.set_error_message(str(e))


    def show_list_clients(self) -> None:
        me = self.client_ctrl._get_current_user()
        if not Permission.read_permission(me, "client"):
            raise PermissionError("Accès refusé.")

        try:
            rows = self.client_ctrl.list_all()
            want_filter = self.view.list_all(rows, has_filter=True)

            if want_filter:
                self.filter_ctrl.show_filter_menu()
        except Exception as e:
            if self.view.app_state:
                self.view.app_state.set_error_message(str(e))

    def show_update_client(self, client_id: int | None = None) -> None:
        me = self._get_current_user()
        # Vérification des permissions afin de lister les clients qui peuvent être modifiés
        if not client_id:
            # Peut il tout update ? On liste tous les clients
            if Permission.update_permission(me, "client"):
                rows = self.client_ctrl.list_all()
            # Peut il seulement update ses propres clients ? On liste ses propres clients
            elif Permission.update_own_permission(me, "client"):
                rows = self.client_ctrl.list_my_clients()
            else:
                raise PermissionError("Accès refusé.")

            # Liste pour selectionner le client à modifier
            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            client_id = selected_id

        # Vérifie encore les permissions dans le cas où l'id est directement fourni
        # Ou même par source de vérité
        owner = self.client_ctrl.get_owner(client_id)
        if not Permission.update_permission(me, "client", owner_id=owner.id):
            raise PermissionError(f"Accès refusé.")

        client_dict = self.client_ctrl.get_client(client_id)
        result = self.view.update_client_flow(client_dict)
        if result is None:
            return

        client_id, payload = result

        try:
            self.client_ctrl.update_client(client_id, payload)
            self.view.app_state.set_success_message("Le client a été mis à jour avec succès.")
        except Exception as e:
            self.view.app_state.set_error_message(str(e))

    def show_update_sales_contact(self, client_id: int | None = None, new_sales_id: int | None = None) -> None:
        me = self.client_ctrl._get_current_user()
        if not Permission.is_admin(me):
            raise PermissionError("Accès refusé.")

        if not client_id:
            rows = self.client_ctrl.list_all()
            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            client_id = selected_id

        if not new_sales_id:
            sales_list = self.user_ctrl.get_all_users_by_role(ROLE_SALES)
            sales_list = sales_list + self.user_ctrl.get_all_users_by_role(ROLE_ADMIN)
            selected_id = self.user_view.list_users(
                sales_list,
                selector=True,
                prompt="[yellow]Sélectionnez un nouveau contact commercial...[/yellow]",
            )
            if selected_id is None:
                return
            new_sales_id = selected_id

        payload = {"sales_contact_id": new_sales_id}

        try:
            self.client_ctrl.update_client(client_id, payload)
            self.user_view.app_state.set_success_message(
                "Le contact commercial a été mis à jour avec succès."
            )
        except Exception as e:
            self.user_view.app_state.set_error_message(str(e))

    def show_delete_client(self, client_id: int | None = None) -> None:
        me = self.client_ctrl._get_current_user()

        if not Permission.is_admin(me):
            raise PermissionError("Accès refusé.")

        if not client_id:
            rows = self.client_ctrl.list_all()
            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            client_id = selected_id

        if not Validations.confirm_action(
            f"Êtes-vous sûr de vouloir supprimer le client '#{client_id}' ?"
        ):
            self.view.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            return

        try:
            self.client_ctrl.delete_client(client_id)
            self.view.app_state.set_success_message("Le client a été supprimé avec succès.")
        except Exception as e:
            self.view.app_state.set_error_message(str(e))