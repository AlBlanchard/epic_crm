from ..views.view import BaseView
from ..utils.app_state import AppState
from ..database import SessionLocal
from ..errors.exceptions import UserCancelledInput
from typing import Any, Dict
from ..utils.validations import Validations
from decimal import Decimal


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

    def list_contracts(
        self,
        rows: list[dict],
        selector: bool = False,
    ) -> int | None:
        self._clear_screen()

        self._print_table(
            "[cyan]Contrats[/cyan]",
            [
                "id",
                "client_name",
                "amount_total",
                "amount_due",
                "is_signed",
                "sales_contact_name",
                "created_at",
                "updated_at",
            ],
            rows,
        )

        if selector:
            validate_number = Validations.validate_number
            self.console.print("[dim]Sélectionnez un contrat...[/dim]")
            str_contract_id = self.get_valid_input(
                "ID du contrat",
                validate=validate_number,
                list_to_compare=[str(u["id"]) for u in rows],
            )
            return int(str_contract_id)

        self.console.print("\n[dim]Appuyez sur Entrée pour revenir au menu...[/dim]")
        self.app_state.display_error_or_success_message()
        self.console.input()

    def update_contract_flow(self, contract_dict: dict) -> tuple[int, dict] | None:
        self._clear_screen()
        try:
            contract_id = contract_dict["id"]
            current_amount_total = contract_dict["amount_total"]
            current_amount_due = contract_dict["amount_due"]
            current_is_signed = contract_dict["is_signed"]

            self.console.print(
                f"[cyan]Modification du contrat [bold]{contract_id}[/bold][/cyan]\n"
            )

            amount_total = self.get_valid_input(
                "Montant total",
                default=str(current_amount_total),
            )
            amount_due = self.get_valid_input(
                "Montant dû",
                default=str(current_amount_due),
            )

            with SessionLocal() as session:
                self.console.print("[dim]Mise à jour du contrat...[/dim]")

                payload: dict = {
                    "amount_total": float(amount_total),
                    "amount_due": float(amount_due),
                }

            return contract_id, payload

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))
            return None

    def sign_contract_flow(self):
        return Validations.confirm_action("Marquer le contrat comme signé ?")

    def add_payment_flow(self, amount_total: Decimal, amount_due: Decimal) -> Decimal:
        try:
            self._clear_screen()
            self.console.print("[cyan]Ajouter un paiement au contrat[/cyan]\n")
            self.console.print(f"Montant total : {amount_total} €")
            self.console.print(f"Restant dû : {amount_due} €\n")

            payment_str = self.get_valid_input(
                "Montant du paiement",
            )
            payment_amount = Decimal(payment_str)
            return payment_amount

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))
            return Decimal(0)
