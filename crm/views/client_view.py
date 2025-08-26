from ..views.view import BaseView
from ..utils.app_state import AppState
from ..database import SessionLocal
from ..errors.exceptions import UserCancelledInput
from typing import Any, Dict, List, Optional
from ..utils.validations import Validations
from ..utils.pretty import Pretty


class ClientView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()

    def create_client_flow(self, sales_contact_id: int) -> Dict[str, Any] | None:
        try:
            self._clear_screen()
            self._print_back_choice()

            full_name = self.get_valid_input(
                "Nom complet", validate=self.valid.validate_str_max_length
            )
            email = self.get_valid_input("Email", validate=self.valid.validate_email)
            phone = self.get_valid_input(
                "Téléphone", validate=self.valid.validate_phone
            )
            company_name = self.get_valid_input(
                "Nom de l'entreprise",
                validate=lambda v: self.valid.validate_str_max_length(
                    str(v), max_length=200
                ),
            )

            with SessionLocal() as session:
                self.console.print("[dim]Création du client...[/dim]")

                payload: dict = {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "company_name": company_name,
                    "sales_contact_id": sales_contact_id,
                }

            return payload

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))

    def list_all(
        self,
        rows: List[Dict[str, Any]],
        selector: bool = False,
        has_filter: bool = False,
    ) -> Optional[int]:

        for row in rows:
            row["email"] = Pretty.pretty_email(row["email"])

        columns = [
            "id",
            ("full_name", "Nom du client"),
            "email",
            ("phone", "Téléphone"),
            ("company_name", "Société"),
            ("sales_contact_name", "Contact commercial"),
        ]
        return self.list_entities(
            rows=rows,
            title="[cyan]Clients[/cyan]",
            columns=columns,
            selector=selector,
            entity="client",
            has_filter=has_filter,
        )

    def update_client_flow(self, client_dict: dict) -> tuple[int, dict] | None:
        self._clear_screen()
        self._print_back_choice()
        try:
            client_id = client_dict["id"]
            current_full_name = client_dict["full_name"]
            current_email = client_dict["email"]
            current_phone = client_dict["phone"]
            current_company_name = client_dict["company_name"]

            full_name = self.get_valid_input(
                "Nom complet",
                default=current_full_name,
                validate=self.valid.validate_str_max_length,
            )
            email = self.get_valid_input(
                "Email", default=current_email, validate=self.valid.validate_email
            )
            phone = self.get_valid_input(
                "Téléphone", default=current_phone, validate=self.valid.validate_phone
            )
            company_name = self.get_valid_input(
                "Nom de l'entreprise",
                default=current_company_name,
                validate=lambda v: self.valid.validate_str_max_length(
                    str(v), max_length=200
                ),
            )

            payload: dict = {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "company_name": company_name,
            }

            return client_id, payload

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))
