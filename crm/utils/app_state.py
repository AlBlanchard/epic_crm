"""Module contenant la classe AppState (version Rich)."""

from __future__ import annotations
from typing import Optional, Dict, Callable
from rich.console import Console


class AppState:
    """Classe utilitaire pour gérer l'état global de l'application et l'afficher avec Rich."""

    _success_message: Optional[str] = None
    _error_message: Optional[str] = None
    _neutral_message: Optional[str] = None

    # --- Styles / rendu ---
    _console = Console()
    _styles: Dict[str, str] = {
        "success": "bold green",
        "error": "bold red",
        "neutral": "yellow",
    }

    # --------- Great Success ! ---------
    @classmethod
    def set_success_message(cls, message: str) -> None:

        cls.clear_all_messages()
        cls._success_message = message

    @classmethod
    def get_success_message(cls) -> Optional[str]:
        return cls._success_message

    @classmethod
    def clear_success_message(cls) -> None:
        cls._success_message = None

    @classmethod
    def has_success(cls) -> bool:
        return cls._success_message is not None

    @classmethod
    def success_message(cls) -> Optional[str]:
        msg = cls.get_success_message()
        cls.clear_success_message()
        return msg

    # --------- Error ----------
    @classmethod
    def set_error_message(cls, message: str) -> None:
        cls.clear_all_messages()
        cls._error_message = message

    @classmethod
    def get_error_message(cls) -> Optional[str]:
        return cls._error_message

    @classmethod
    def clear_error_message(cls) -> None:
        cls._error_message = None

    @classmethod
    def has_error(cls) -> bool:
        return cls._error_message is not None

    @classmethod
    def error_message(cls) -> Optional[str]:
        msg = cls.get_error_message()
        cls.clear_error_message()
        return msg

    # --------- Neutral --------
    @classmethod
    def set_neutral_message(cls, message: str) -> None:
        cls.clear_all_messages()
        cls._neutral_message = message

    @classmethod
    def get_neutral_message(cls) -> Optional[str]:
        return cls._neutral_message

    @classmethod
    def clear_neutral_message(cls) -> None:
        cls._neutral_message = None

    @classmethod
    def has_neutral(cls) -> bool:
        return cls._neutral_message is not None

    @classmethod
    def neutral_message(cls) -> Optional[str]:
        msg = cls.get_neutral_message()
        cls.clear_neutral_message()
        return msg

    # --------- Display --------
    @classmethod
    def display_error_or_success_message(cls) -> None:
        """Affiche un message présent (erreur > succès > neutre) et le consomme."""
        if cls.has_error():
            cls._render_and_consume(kind="error", getter=cls.error_message)
        elif cls.has_success():
            cls._render_and_consume(kind="success", getter=cls.success_message)
        elif cls.has_neutral():
            cls._render_and_consume(kind="neutral", getter=cls.neutral_message)

    @classmethod
    def _render_and_consume(
        cls, *, kind: str, getter: Callable[[], Optional[str]]
    ) -> None:
        msg = getter()
        if not msg:
            return

        style = cls._styles.get(kind, "")
        cls._console.print(f"\n[{style}]{msg}[/{style}]")

    # --------- Clear all -------
    @classmethod
    def clear_all_messages(cls) -> None:
        """Efface tous les messages enregistrés pour éviter les doublons d'affichage."""
        cls.clear_error_message()
        cls.clear_success_message()
        cls.clear_neutral_message()

    @classmethod
    def testprint(cls):
        cls._console.print(cls._error_message)
