import sys
import click
import platform
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional
from sqlalchemy import Table
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..database import SessionLocal
from rich.table import Table
from rich.console import Console
from ..errors.exceptions import UserCancelledInput
from ..utils.app_state import AppState


class BaseView(ABC):
    def __init__(
        self, *, session: Optional[Session] = None, console: Optional[Console] = None
    ):
        self.session = session or SessionLocal()
        self._owns_session = session is None
        self._setup_services()
        self.console = console or Console()

    @abstractmethod
    def _setup_services(self) -> None:
        """Initialise les services spécifiques de la view."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._owns_session and self.session:
            self.session.close()

    @staticmethod
    def _prompt_non_empty(label: str) -> str:
        """Validation minimale côté View : non vide. Le reste => Controller."""
        while True:
            val = click.prompt(label).strip()
            if val:
                return val
            Console().print("[red]Ce champ est requis.[/red]")

    @staticmethod
    def _prompt_optional(label: str) -> Optional[str]:
        val = click.prompt(label, default="", show_default=False).strip()
        return val or None

    @staticmethod
    def _clear_screen():
        """Efface le contenu de la console."""

        user_platform = platform.system().lower()

        if user_platform == "windows":
            os.system("cls")
        else:
            os.system("clear")

    @staticmethod
    def get_valid_input(prompt, validation_func=None, default_value=None):
        """
        Demande une entrée à l'utilisateur et vérifie qu'elle n'est pas vide.
        'q' pour annuler l'entrée.
        prompt : Texte affiché à l'utilisateur.
        validation_func : Fonction de validation optionnelle (défaut : None).
        default_value : Valeur par défaut optionnelle (défaut : None).
        """
        original_prompt = prompt

        while True:
            if default_value:
                full_prompt = f"{original_prompt} (défaut : {default_value}) : "
            else:
                full_prompt = f"{original_prompt} : "

            user_input = input(full_prompt).strip()

            if user_input == "q":
                raise UserCancelledInput("Action annulée par l'utilisateur.")

            if not user_input and not default_value:
                print("--> Ce champ est obligatoire. Veuillez réessayer.\n")
                continue

            if not user_input and default_value:
                return default_value

            if validation_func:
                try:
                    validation_func(user_input)

                except Exception as e:
                    AppState.set_error_message(str(e))

            # Efface le message d'erreur s'il y a eu une mauvaise saise
            # Pour éviter de l'afficher à tort au menu suivant
            AppState.clear_error_message()
            return user_input

    def print_quit_option(self) -> None:
        self.console.print("[dim]0. Quitter[/dim]")

    def ask_choice(self, prompt: str = "\nChoix", *, allow_quit: bool = True) -> int:
        while True:
            try:
                value = click.prompt(prompt, type=int)
                if not allow_quit and value == 0:
                    self.console.print("[red]0 est réservé à 'Quitter'.[/red]")
                    continue
                return value
            except click.Abort:
                # Ctrl+C propre
                raise
            except Exception:
                self.console.print("[red]Veuillez entrer un nombre valide.[/red]")

    def handle_quit(self, *, farewell: str = "[bold cyan]\nA bientôt !\n[bold cyan]"):
        self.console.print(farewell)
        self.session.close()
        sys.exit(0)

    def _print_table(
        self, title: str, columns: List[str], rows: List[Dict[str, Any]]
    ) -> None:
        table = Table(title=title)
        for col in columns:
            table.add_column(col, overflow="fold")
        for r in rows:
            table.add_row(*[str(r.get(c, "")) for c in columns])
        self.console.print(table)
