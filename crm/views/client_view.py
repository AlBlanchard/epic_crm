from ..views.view import BaseView
from ..utils.app_state import AppState
from ..database import SessionLocal
from ..errors.exceptions import UserCancelledInput
from typing import Any, Dict
from ..utils.validations import Validations


class ClientView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()

    @staticmethod
    def _asdict_user(o: Any) -> Dict[str, Any]:
        if isinstance(o, dict):
            return o

        return {
            "id": getattr(o, "id", ""),
            "full_name": getattr(o, "full_name", ""),
            "email": getattr(o, "email", ""),
            "phone": getattr(o, "phone", ""),
            "company_name": getattr(o, "company_name", ""),
            "sales_contact_id": getattr(o, "sales_contact_id", ""),
            "created_at": getattr(o, "created_at", ""),
        }

    def create_client_flow(self, sales_contact_id: int):
        try:
            self._clear_screen()

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
        users_name_tuples: list[tuple[int, str]],
        selector: bool = False,
    ) -> int | None:
        self._clear_screen()

        id_to_name = dict(users_name_tuples)

        # Convertit chaque row (client) en dict prêt pour affichage
        rows = [self._asdict_user(r) for r in rows]

        # Remplace sales_contact_id par le nom
        for row in rows:
            sales_id = row.get("sales_contact_id")
            if sales_id is not None:
                row["sales_contact"] = id_to_name.get(sales_id, f"#{sales_id}")
            else:
                row["sales_contact"] = "Non assigné"
            row.pop("sales_contact_id", None)  # supprime l'ID

        # Affichage
        self._print_table(
            "[cyan]Clients[/cyan]",
            [
                "id",
                "full_name",
                "email",
                "phone",
                "company_name",
                "sales_contact",
            ],
            rows,
        )

        if selector:
            validate_number = Validations.validate_number
            self.console.print("[dim]Sélectionnez un client...[/dim]")
            str_client_id = self.get_valid_input(
                "ID du client",
                validate=validate_number,
                list_to_compare=[str(u["id"]) for u in rows],
            )
            return int(str_client_id)

        self.console.print("\n[dim]Appuyez sur Entrée pour revenir au menu...[/dim]")
        self.app_state.display_error_or_success_message()
        self.console.input()
