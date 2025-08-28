from ..controllers.base import AbstractController
from ..views.event_view import EventView
from ..controllers.event_controller import EventController
from ..controllers.filter_controller import FilterController
from ..controllers.user_controller import UserController
from ..controllers.contract_controller import ContractController
from ..views.contract_view import ContractView
from ..views.user_view import UserView
from ..auth.permission import Permission
from ..utils.validations import Validations

class EventMenuController(AbstractController):
    def _setup_services(self) -> None:
        self.view = EventView()
        self.event_ctrl = EventController()
        self.filter_ctrl = FilterController()
        self.user_ctrl = UserController()
        self.contract_ctrl = ContractController()
        self.contract_view = ContractView()
        self.user_view = UserView()

    def show_create_event(self, contract_id: int | None = None) -> None:
        me = self._get_current_user()
        if not Permission.create_permission(me, "event"):
            raise PermissionError("Accès refusé.")

        # Sélection du contrat à qui sera attaché l'événement
        if not contract_id:
            # Peut il tout update ? On liste tous les contrats
            if Permission.update_permission(me, "contract"):
                rows = self.contract_ctrl.list_signed_contracts()
            # Peut il seulement update ses propres contrats ? On liste ses propres contrats
            elif Permission.update_own_permission(me, "contract"):
                rows = self.contract_ctrl.list_signed_contracts(sales_contact_id=me.id)
            else:
                raise PermissionError("Accès refusé.")

            # Liste pour selectionner le contrat à modifier
            selected_id = self.contract_view.list_all(
                rows, selector=True, title="Contrats Signés"
            )
            if selected_id is None:
                return
            contract_id = selected_id

        result = self.view.create_event_flow(contract_id)
        if result is None:
            return

        data = result

        try:
            self.event_ctrl.create_event(data)
            self.view.app_state.set_success_message("L'événement a été créé avec succès.")
        except Exception as e:
            if self.view.app_state:
                self.view.app_state.set_error_message(str(e))

    def show_list_events(self):
        me = self._get_current_user()
        if not Permission.read_permission(me, "event"):
            raise PermissionError("Accès refusé.")

        try:
            rows = self.event_ctrl.list_all()
            want_filter = self.view.list_all(rows, has_filter=True)

            if want_filter:
                self.filter_ctrl.show_filter_menu()
        except Exception as e:
            if self.view.app_state:
                self.view.app_state.set_error_message(str(e))
                self.view.app_state.set_error_message(str(e))

    def show_update_event(self, event_id: int | None = None) -> None:
        me = self._get_current_user()

        if event_id:
            if not Permission.update_permission(me, "event", event_id):
                raise PermissionError("Accès refusé.")

        if not event_id:
            if Permission.update_permission(me, "event"):
                rows = self.event_ctrl.list_all()
            elif Permission.update_own_permission(me, "event"):
                rows = self.event_ctrl.list_my_events()
            else:
                raise PermissionError("Accès refusé.")

            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            event_id = selected_id

        event = self.event_ctrl.get_event(event_id)
        new_data = self.view.update_event_flow(event)

        if not new_data:
            return

        try:
            self.event_ctrl.update_event(event_id, new_data)
            self.view.app_state.set_success_message("L'événement a été mis à jour avec succès.")
        except Exception as e:
            self.view.app_state.set_error_message(str(e))

    def show_add_event_note(self, event_id: int | None = None):
        me = self.event_ctrl._get_current_user()
        if not Permission.update_permission(me, "event", event_id):
            raise PermissionError("Accès refusé.")

        if not event_id:
            if Permission.update_permission(me, "event"):
                rows = self.event_ctrl.list_all()
            elif Permission.update_own_permission(me, "event"):
                rows = self.event_ctrl.list_my_events()
            else:
                raise PermissionError("Accès refusé.")

            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            event_id = selected_id

        note = self.view.add_event_note_flow()

        try:
            self.event_ctrl.create_note(event_id, note)
            self.view.app_state.set_success_message("La note a été ajoutée avec succès.")
        except Exception as e:
            self.view.app_state.set_error_message(str(e))

    def show_delete_note(self, event_id: int | None = None):
        me = self._get_current_user()
        if not Permission.update_permission(me, "event", event_id):
            raise PermissionError("Accès refusé.")

        if not event_id:
            if Permission.update_permission(me, "event"):
                rows = self.event_ctrl.list_all()
            elif Permission.update_own_permission(me, "event"):
                rows = self.event_ctrl.list_my_events()
            else:
                raise PermissionError("Accès refusé.")

            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            event_id = selected_id

        notes_list = self.event_ctrl.list_event_notes(event_id)
        selected_note_id = self.view.list_notes(notes_list, selector=True)
        if selected_note_id is None:
            return

        try:
            self.event_ctrl.delete_note(event_id, selected_note_id)
            self.view.app_state.set_success_message("La note a été supprimée avec succès.")
        except Exception as e:
            self.view.app_state.set_error_message(str(e))

    def show_update_support(self, event_id: int | None = None, new_support_id: int | None = None) -> None:
        me = self.event_ctrl._get_current_user()
        if not Permission.update_permission(me, "event", event_id):
            raise PermissionError("Accès refusé.")

        if not event_id:
            if Permission.update_permission(me, "event"):
                rows = self.event_ctrl.list_all()
            elif Permission.update_own_permission(me, "event"):
                rows = self.event_ctrl.list_my_events()
            else:
                raise PermissionError("Accès refusé.")

            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            event_id = selected_id

        if not new_support_id:
            if Permission.read_permission(me, "user"):
                rows = self.user_ctrl.get_all_users_by_role("support")
            else:
                raise PermissionError("Accès refusé.")

            selected_id = self.user_view.list_users(rows, selector=True)
            if selected_id is None:
                return
            new_support_id = selected_id

        payload = {}
        if new_support_id:
            payload["support_contact_id"] = new_support_id

        try:
            self.event_ctrl.update_event(event_id, payload)
            self.view.app_state.set_success_message("L'événement a été mis à jour avec succès.")
        except Exception as e:
            self.view.app_state.set_error_message(str(e))

    def show_delete_event(self, event_id: int | None = None):
        me = self.event_ctrl._get_current_user()
        if not Permission.delete_permission(me, "event", event_id):
            raise PermissionError("Accès refusé.")

        if not event_id:
            if Permission.delete_permission(me, "event"):
                rows = self.event_ctrl.list_all()
            elif Permission.delete_own_permission(me, "event"):
                rows = self.event_ctrl.list_my_events()
            else:
                raise PermissionError("Accès refusé.")

            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            event_id = selected_id

        if not Validations.confirm_action(
            f"Êtes-vous sûr de vouloir supprimer l'événement '#{event_id}' ?"
        ):
            self.view.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            return

        try:
            self.event_ctrl.delete_event(event_id)
            self.view.app_state.set_success_message("L'événement a été supprimé avec succès.")
        except Exception as e:
            self.view.app_state.set_error_message(str(e))