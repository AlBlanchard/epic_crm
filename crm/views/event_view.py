from ..views.view import BaseView
from ..utils.app_state import AppState
from ..database import SessionLocal
from ..errors.exceptions import UserCancelledInput
from typing import Any, Dict, List
from ..utils.validations import Validations
from decimal import Decimal


class EventView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()

    def create_event_flow(self, contract_id: int) -> Dict[str, Any]:
        try:
            self._clear_screen()

            event_location = self.get_valid_input("Lieu de l'événement")
            event_attendees = self.get_valid_input(
                "Nombre de participants", transform=int
            )

            event_start_date = self.get_date_input("Date de l'événement")
            Validations.validate_future_datetime(event_start_date)
            event_end_date = self.get_date_input("Date de fin de l'événement")
            Validations.validate_future_datetime(event_end_date)
            Validations.validate_date_order(event_start_date, event_end_date)

            with SessionLocal() as session:
                self.console.print("[dim]Création de l'événement...[/dim]")

                payload: dict = {
                    "contract_id": contract_id,
                    "date_start": event_start_date,
                    "date_end": event_end_date,
                    "location": event_location,
                    "attendees": event_attendees,
                }

            return payload

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))
            return {}

    def list_events(
        self,
        rows: list[dict],
        selector: bool = False,
    ) -> int | None:
        self._clear_screen()

        for row in rows:
            row["date_start"] = self.pretty_datetime(row["date_start"])
            row["date_end"] = self.pretty_datetime(row["date_end"])

        self._print_table(
            "[cyan]Evénements[/cyan]",
            [
                "id",
                "client_name",
                "client_contact",
                "date_start",
                "date_end",
                "support_contact_name",
                "location",
                "attendees",
                "notes",
            ],
            rows,
        )

        if selector:
            validate_number = Validations.validate_number
            self.console.print("[dim]Sélectionnez un event...[/dim]")
            str_event_id = self.get_valid_input(
                "ID de l'événement",
                validate=validate_number,
                list_to_compare=[str(u["id"]) for u in rows],
            )
            return int(str_event_id)

        self.console.print("\n[dim]Appuyez sur Entrée pour revenir au menu...[/dim]")
        self.app_state.display_error_or_success_message()
        self.console.input()

    def update_event_flow(self, event: dict) -> Dict[str, Any]:
        try:
            self._clear_screen()
            self.console.print("[dim]Mise à jour de l'événement...[/dim]")
            current_location = event["location"]
            current_attendees = event["attendees"]
            current_date_start = event["date_start"]
            current_date_end = event["date_end"]

            location = self.get_valid_input(
                "Lieu de l'événement", default=current_location
            )
            attendees = self.get_valid_input(
                "Nombre de participants", default=current_attendees, transform=int
            )
            date_start = self.get_date_input(
                "\n- Date de début de l'événement -", default=current_date_start
            )
            date_end = self.get_date_input(
                "\n- Date de fin de l'événement -", default=current_date_end
            )

            Validations.validate_future_datetime(date_start)
            Validations.validate_future_datetime(date_end)
            Validations.validate_date_order(date_start, date_end)

            payload: dict = {
                "location": location,
                "attendees": attendees,
                "date_start": date_start,
                "date_end": date_end,
            }

            return payload

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))
            return {}

    def add_event_note_flow(self) -> str:
        self._clear_screen()
        self.console.print("[cyan]Ajout d'une note à l'événement[/cyan]")
        note = self.get_valid_input("Entrez votre note", transform=str)

        return note

    def list_notes(
        self,
        rows: list[dict],
        selector: bool = False,
    ) -> int | None:
        self._clear_screen()

        self._print_table(
            "[cyan]Notes[/cyan]",
            ["id", "note", "created_at"],
            rows,
        )

        if selector:
            validate_number = Validations.validate_number
            self.console.print("[dim]Sélectionnez une note...[/dim]")
            str_note_id = self.get_valid_input(
                "ID de la note",
                validate=validate_number,
                list_to_compare=[str(u["id"]) for u in rows],
            )
            return int(str_note_id)

        self.console.print("\n[dim]Appuyez sur Entrée pour revenir au menu...[/dim]")
        self.app_state.display_error_or_success_message()
        self.console.input()
