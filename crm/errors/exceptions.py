from ..utils.app_state import AppState


class UserCancelledInput(Exception):
    """Exception levée lorsque l'utilisateur annule une action."""

    def __init__(self, message="Action annulée. Retour au menu précédent."):
        super().__init__(message)
        self.message = message
        AppState.set_neutral_message(self.message)
