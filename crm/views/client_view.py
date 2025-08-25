from ..views.view import BaseView
from ..utils.app_state import AppState
from ..database import SessionLocal
from ..errors.exceptions import UserCancelledInput
from typing import Any, Dict
from ..utils.validations import Validations


class ClientView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()

    def create_client_flow(self, sales_contact_id: int) -> Dict[str, Any] | None:
        try:
            self._clear_screen()
            self._print_back_choice()

            full_name = self.get_valid_input("Nom complet")
            email = self.get_valid_input("Email")
            phone = self.get_valid_input("Téléphone")
            company_name = self.get_valid_input("Nom de l'entreprise")

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

    def list_clients(
        self,
        rows: list[dict],
        selector: bool = False,
    ) -> int | None:
        self._clear_screen()

        self._print_table(
            "[cyan]Clients[/cyan]",
            [
                "id",
                "full_name",
                "email",
                "phone",
                "company_name",
                "sales_contact_name",
            ],
            rows,
        )

        if selector:
            validate_number = Validations.validate_number
            self.console.print("[dim]Sélectionnez un client...[/dim]")
            self._print_back_choice()
            str_client_id = self.get_valid_input(
                "ID du client",
                validate=validate_number,
                list_to_compare=[str(u["id"]) for u in rows],
            )
            return int(str_client_id)

        self.console.print("\n[dim]Appuyez sur Entrée pour revenir au menu...[/dim]")
        self.app_state.display_error_or_success_message()
        self.console.input()

    def update_client_flow(self, client_dict: dict) -> tuple[int, dict] | None:
        self._clear_screen()
        self._print_back_choice()
        try:
            client_id = client_dict["id"]
            current_full_name = client_dict["full_name"]
            current_email = client_dict["email"]
            current_phone = client_dict["phone"]
            current_company_name = client_dict["company_name"]

            full_name = self.get_valid_input("Nom complet", default=current_full_name)
            email = self.get_valid_input("Email", default=current_email)
            phone = self.get_valid_input("Téléphone", default=current_phone)
            company_name = self.get_valid_input(
                "Nom de l'entreprise", default=current_company_name
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
