from ..views.view import BaseView
from ..utils.app_state import AppState
from ..database import SessionLocal
from ..errors.exceptions import UserCancelledInput
from typing import Any, Dict
from ..utils.validations import Validations


class ContractView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()

    def create_contract_flow(self, client_id: int) -> Dict[str, Any]:
        try:
            self._clear_screen()

            amount_total = self.get_valid_input("Montant total")
            amount_due = self.get_valid_input("Montant dû")
            is_signed = Validations.confirm_action("Contrat signé ?")

            with SessionLocal() as session:
                self.console.print("[dim]Création du contrat...[/dim]")

                payload: dict = {
                    "client_id": client_id,
                    "amount_total": float(amount_total),
                    "amount_due": float(amount_due),
                    "is_signed": is_signed,
                }

            return payload

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))
            return {}
