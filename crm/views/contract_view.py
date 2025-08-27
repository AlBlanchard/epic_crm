from ..views.view import BaseView
from ..utils.app_state import AppState
from ..database import SessionLocal
from ..errors.exceptions import UserCancelledInput
from typing import Any, Dict, List, Optional
from ..utils.validations import Validations
from ..utils.pretty import Pretty
from decimal import Decimal


class ContractView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()

    def create_contract_flow(self, client_id: int) -> Dict[str, Any]:
        try:
            self._clear_screen()
            self._print_back_choice()

            amount_total = self.get_valid_input(
                "Montant total",
                validate=Validations.validate_currency,
            )
            amount_due = self.get_valid_input(
                "Montant dû",
                validate=Validations.validate_currency,
            )
            is_signed = Validations.confirm_action("Contrat signé ?")

            with SessionLocal() as session:
                self.console.print("[dim]Création du contrat...[/dim]")

                payload: dict = {
                    "client_id": client_id,
                    "amount_total": Decimal(amount_total),
                    "amount_due": Decimal(amount_due),
                    "is_signed": is_signed,
                }

            return payload

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))
            return {}

    def list_all(
        self,
        rows: List[Dict[str, Any]],
        selector: bool = False,
        has_filter: bool = False,
        title: str = "Contrats",
    ) -> Optional[int]:

        for row in rows:
            row["created_at"] = Pretty.pretty_datetime(row["created_at"])
            row["updated_at"] = Pretty.pretty_datetime(row["updated_at"])
            row["amount_total"] = Pretty.pretty_currency(row["amount_total"])
            row["amount_due"] = Pretty.pretty_currency(row["amount_due"], debt=True)
            row["is_signed"] = Pretty.pretty_bool(row["is_signed"])

        columns = [
            "id",
            ("client_name", "Client"),
            ("amount_total", "Total"),
            ("amount_due", "Restant dû"),
            ("is_signed", "Signé ?"),
            ("sales_contact_name", "Commercial"),
            ("created_at", "Créé le"),
            ("updated_at", "Modifié le"),
        ]
        return self.list_entities(
            rows=rows,
            title=f"[cyan]{title}[/cyan]",
            columns=columns,
            selector=selector,
            entity="contrat",
            has_filter=has_filter,
        )

    def update_contract_flow(self, contract_dict: dict) -> tuple[int, dict] | None:
        self._clear_screen()
        self._print_back_choice()
        try:
            contract_id = contract_dict["id"]
            current_amount_total = contract_dict["amount_total"]
            current_amount_due = contract_dict["amount_due"]

            self.console.print(
                f"[cyan]Modification du contrat [bold]{contract_id}[/bold][/cyan]\n"
            )

            amount_total = self.get_valid_input(
                "Montant total",
                default=str(current_amount_total),
                validate=Validations.validate_currency,
                transform=Decimal,
            )
            amount_due = self.get_valid_input(
                "Montant dû",
                default=str(current_amount_due),
                validate=Validations.validate_currency,
                transform=Decimal,
            )

            with SessionLocal() as session:
                self.console.print("[dim]Mise à jour du contrat...[/dim]")

                payload: dict = {
                    "amount_total": Decimal(amount_total),
                    "amount_due": Decimal(amount_due),
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
            self._print_back_choice()

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
