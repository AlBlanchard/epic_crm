from ..views.view import BaseView
from ..utils.app_state import AppState
from ..database import SessionLocal
from ..errors.exceptions import UserCancelledInput
from typing import Any, Dict
from ..utils.validations import Validations
from ..utils.pretty import Pretty


class EventView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()

    def create_event_flow(self, contract_id: int) -> Dict[str, Any]:
        try:
            self._clear_screen()
            self._print_back_choice()

            event_location = self.get_valid_input(
                "Lieu de l'événement",
                validate=lambda v: self.valid.validate_str_max_length(
                    str(v), max_length=300
                ),
            )
            event_attendees = self.get_valid_input(
                "Nombre de participants",
                validate=self.valid.validate_positive_integer,
                transform=int,
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

    def list_all(
        self, rows: list[dict], selector: bool = False, has_filter: bool = False
    ) -> int | None:
        self._clear_screen()

        for row in rows:
            row["date_start"] = Pretty.pretty_datetime(row["date_start"])
            row["date_end"] = Pretty.pretty_datetime(row["date_end"])
            row["client_contact"] = Pretty.pretty_contact(row["client_contact"])
            row["notes"] = Pretty.pretty_notes(row["notes"])

        columns = [
            "id",
            ("client_name", "Client"),
            ("client_contact", "Contact du Client"),
            ("date_start", "Début"),
            ("date_end", "Fin"),
            ("support_contact_name", "Support"),
            ("location", "Lieu"),
            ("attendees", "Nbr d'invités"),
            ("notes", "Notes"),
        ]
        return self.list_entities(
            rows=rows,
            title="[cyan]Evénements[/cyan]",
            columns=columns,
            selector=selector,
            entity="événement",
            has_filter=has_filter,
        )

    def update_event_flow(self, event: dict) -> Dict[str, Any]:
        try:
            self._clear_screen()
            self.console.print("[dim]Mise à jour de l'événement...[/dim]")
            current_location = event["location"]
            current_attendees = event["attendees"]
            current_date_start = event["date_start"]
            current_date_end = event["date_end"]

            self._print_back_choice()

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
        self._print_back_choice()
        note = self.get_valid_input("Entrez votre note", transform=str)

        return note

    def list_notes(
        self,
        rows: list[dict],
        selector: bool = False,
    ) -> int | None:
        for row in rows:
            row["created_at"] = Pretty.pretty_datetime(row["created_at"])
            row["note"] = Pretty.pretty_notes([row["note"]])

        columns = [
            "id",
            ("note", "Note"),
            ("created_at", "Date de création"),
        ]

        return self.list_entities(
            rows=rows,
            title="[cyan]Notes[/cyan]",
            columns=columns,
            selector=selector,
            entity="event_note",
        )
