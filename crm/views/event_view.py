from ..views.view import BaseView
from ..utils.app_state import AppState
from ..database import SessionLocal
from ..errors.exceptions import UserCancelledInput
from typing import Any, Dict
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
