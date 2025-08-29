from ..controllers.base import AbstractController
from ..views.contract_view import ContractView
from ..controllers.contract_controller import ContractController
from ..controllers.filter_controller import FilterController
from ..controllers.user_controller import UserController
from ..controllers.client_controller import ClientController
from ..views.client_view import ClientView
from ..auth.permission import Permission
from ..errors.exceptions import UserCancelledInput
from decimal import Decimal
from ..utils.validations import Validations


class ContractMenuController(AbstractController):
    def _setup_services(self) -> None:
        self.view = ContractView()
        self.contract_ctrl = ContractController()
        self.filter_ctrl = FilterController()
        self.user_ctrl = UserController()
        self.client_ctrl = ClientController()
        self.client_view = ClientView()

    def show_create_contract(self, client_id: int | None = None) -> None:
        me = self.user_ctrl._get_current_user()

        if not Permission.create_permission(me, "contract"):
            raise PermissionError("Accès refusé.")

        # Sélection du client à qui sera attaché le contrat
        if not client_id:
            rows = self.client_ctrl.list_all()
            selected_id = self.client_view.list_all(rows, selector=True)
            if selected_id is None:
                return
            client_id = selected_id

        result = self.view.create_contract_flow(client_id)
        if result is None:
            return

        data = result

        try:
            self.contract_ctrl.create_contract(data)
            self.view.app_state.set_success_message(
                "Le contrat a été créé avec succès."
            )
        except Exception as e:
            if self.view.app_state:
                self.view.app_state.set_error_message(str(e))

    def show_list_contracts(self):
        me = self.user_ctrl._get_current_user()
        if not Permission.read_permission(me, "contract"):
            raise PermissionError("Accès refusé.")

        rows = self.contract_ctrl.list_all()
        want_filter = self.view.list_all(rows, has_filter=True)

        if want_filter:
            self.filter_ctrl.show_filter_menu(entity="contracts")

    def show_sign_contract(self, contract_id: int | None = None):
        me = self._get_current_user()

        # Vérification des permissions afin de lister les contrats qui peuvent être modifiés
        if not contract_id:
            # Peut il tout update ? On liste tous les contrats
            if Permission.update_permission(me, "contract"):
                rows = self.contract_ctrl.list_unsigned_contracts()
            # Peut il seulement update ses propres contrats ? On liste ses propres contrats
            elif Permission.update_own_permission(me, "contract"):
                rows = self.contract_ctrl.list_unsigned_contracts(
                    sales_contact_id=me.id
                )
            else:
                raise PermissionError("Accès refusé.")

            # Liste pour selectionner le contrat à modifier
            selected_id = self.view.list_all(
                rows, selector=True, title="Contrats Non Signés"
            )
            if selected_id is None:
                return
            contract_id = selected_id

        # Vérifie encore les permissions dans le cas où l'id est directement fourni
        # Ou même par source de vérité
        owner = self.contract_ctrl.get_contract_owner(contract_id)
        if not Permission.update_permission(me, "contract", owner_id=owner.id):
            raise PermissionError(f"Accès refusé.")

        if self.contract_ctrl.is_contract_signed(contract_id):
            raise PermissionError("Le contrat est déjà signé.")

        is_signed = self.view.sign_contract_flow()
        if is_signed is None:
            raise UserCancelledInput("Action annulée par l'utilisateur.")

        payload: dict = {"is_signed": is_signed}

        try:
            self.contract_ctrl.update_contract(contract_id, payload)
            self.view.app_state.set_success_message(
                "Le contrat a été mis à jour avec succès."
            )
        except Exception as e:
            self.view.app_state.set_error_message(str(e))

    def show_update_contract_amount(
        self, contract_id: int | None = None, payment_amount: Decimal | None = None
    ):
        me = self._get_current_user()

        if not contract_id:
            if Permission.update_permission(me, "contract"):
                rows = self.contract_ctrl.list_all()
            elif Permission.update_own_permission(me, "contract"):
                rows = self.contract_ctrl.list_my_contracts()
            else:
                raise PermissionError("Accès refusé.")

            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            contract_id = selected_id

        owner_id = self.contract_ctrl.get_contract_owner(contract_id).id
        if not Permission.update_permission(me, "contract", owner_id=owner_id):
            raise PermissionError("Accès refusé.")

        amount_total, amount_due = self.contract_ctrl.get_contract_amounts(contract_id)

        if not payment_amount:
            payment_amount = self.view.add_payment_flow(amount_total, amount_due)

        new_amount_due = amount_due - payment_amount

        if new_amount_due < 0:
            raise ValueError("Le montant total ne peut pas être dépassé.")

        payload = {"amount_due": new_amount_due}

        try:
            self.contract_ctrl.update_contract(contract_id, payload)
            self.view.app_state.set_success_message(
                "Le montant du contrat a été mis à jour avec succès."
            )
        except Exception as e:
            self.view.app_state.set_error_message(str(e))

    def show_delete_contract(self, contract_id: int | None = None):
        me = self.contract_ctrl._get_current_user()
        if not Permission.delete_permission(me, "contract", contract_id):
            raise PermissionError("Accès refusé.")

        if not contract_id:
            if Permission.delete_permission(me, "contract"):
                rows = self.contract_ctrl.list_all()
            elif Permission.delete_own_permission(me, "contract"):
                rows = self.contract_ctrl.list_my_contracts()
            else:
                raise PermissionError("Accès refusé.")

            selected_id = self.view.list_all(rows, selector=True)
            if selected_id is None:
                return
            contract_id = selected_id

        if not Validations.confirm_action(
            f"Êtes-vous sûr de vouloir supprimer le contrat '#{contract_id}' ?"
        ):
            self.view.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            return

        try:
            self.contract_ctrl.delete_contract(contract_id)
            self.view.app_state.set_success_message(
                "Le contrat a été supprimé avec succès."
            )
        except Exception as e:
            self.view.app_state.set_error_message(str(e))
