import sys
import click
import platform
import os
import calendar
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Callable, TypeVar
from sqlalchemy.orm import Session
from ..database import SessionLocal
from rich.table import Table
from rich.console import Console
from ..errors.exceptions import UserCancelledInput
from ..utils.app_state import AppState
from ..utils.validations import Validations
from getpass import getpass
from datetime import datetime


# Type variable pour des types génériques
# Permet de dire "n'importe quel type en entrée mais ce sera le même type en sortie"
T = TypeVar("T")


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

    def _print_table(
        self, title: str, columns: List[str], rows: List[Dict[str, Any]]
    ) -> None:
        table = Table(title=title)
        for col in columns:
            table.add_column(col, overflow="fold")
        for r in rows:
            table.add_row(*[str(r.get(c, "")) for c in columns])
        self.console.print(table)

    @staticmethod
    def get_valid_input(
        prompt: str,
        *,
        default: Optional[T] = None,
        transform: Optional[Callable[[str], T]] = None,
        validate: Optional[Callable[[T], None]] = None,
        list_to_compare: Optional[Iterable[str]] = None,
        quit_value: str = "q",
        quit_aliases: Iterable[str] = ("q", "quit", "exit"),
        show_default: bool = True,
        max_attempts: Optional[int] = 3,
    ) -> T:
        """
        Demande une entrée utilisateur, transforme et valide.
        - 'default': valeur de repli si entrée vide (gérée par click).
        - 'transform': str -> T (int, float, datetime, objet métier...).
        - 'validate': lève une exception si invalide.
        - 'quit_value'/'quit_aliases': mots clés pour annuler (insensibles à la casse).
        - 'max_attempts': stoppe après N essais (None = illimité).
        """
        attempts = 0
        aliases = {a.casefold().strip() for a in quit_aliases} | {
            quit_value.casefold().strip()
        }

        while True:
            if max_attempts is not None and attempts >= max_attempts:
                AppState.set_error_message("Nombre maximal d'essais atteint.")
                raise ValueError("Essais max atteints, retour au menu.")
            AppState.display_error_or_success_message()
            try:

                raw = click.prompt(prompt, default=default, show_default=show_default)
                raw_str = str(raw).strip()

                # Quit intention
                if raw_str.casefold() in aliases:
                    raise UserCancelledInput("Action annulée par l'utilisateur.")

                if raw_str is None and default is None:
                    AppState.set_error_message("Ce champ est requis.")
                    attempts += 1
                    continue

                # Transform
                try:
                    value: T
                    if transform:
                        value = transform(raw_str)
                    else:
                        # Sans transform, on retourne tel quel (str ou default non-str)
                        value = raw  # type: ignore[assignment]
                except Exception as e:
                    AppState.set_error_message(f"Conversion invalide: {e}")
                    attempts += 1
                    continue

                # Validate
                if validate:
                    try:
                        validate(value)
                    except Exception as e:
                        AppState.set_error_message(str(e))
                        attempts += 1
                        continue

                # Dans la liste
                if list_to_compare is not None:
                    try:
                        str_value = str(value).strip()
                        Validations.is_in_list(str_value, list_to_compare)

                    except Exception as e:
                        AppState.set_error_message(f"{e}")
                        attempts += 1
                        continue

                return value

            except UserCancelledInput:
                # AppState déjà positionné neutre ci-dessus
                raise
            except click.Abort:
                AppState.set_neutral_message("Action annulée par l'utilisateur.")
                raise
            except Exception as e:
                AppState.set_error_message(f"Erreur: {e}")
                attempts += 1
                continue

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

    @staticmethod
    def get_date_input(
        title: str = "Saisir une date", default: datetime | None = None
    ) -> datetime:
        """Demande jour, mois, année, heure, minute et renvoie (datetime, string)."""
        click.echo(title)
        console = Console()

        dt = None

        if default:
            dt = datetime.fromisoformat(str(default))
            default_date_str = BaseView.pretty_datetime(dt)
            console.print(
                f"[dim]Date actuelle: [bold green]{default_date_str}[/bold green][/dim]"
            )

        # Entrées simples (validators à part)
        year = BaseView.get_valid_input(
            "Année (ex: 2025)",
            default=dt.year if dt else None,
            transform=int,
            validate=Validations.validate_year,
        )
        month = BaseView.get_valid_input(
            "Mois (1-12)",
            default=dt.month if dt else None,
            transform=int,
            validate=Validations.validate_month,
        )
        day = BaseView.get_valid_input(
            "Jour (1-31)",
            default=dt.day if dt else None,
            transform=int,
            validate=lambda x: Validations.validate_day_in_month(x, month, year),
        )
        hour = BaseView.get_valid_input(
            "Heure (0-23)",
            default=dt.hour if dt else None,
            transform=int,
            validate=Validations.validate_hour,
        )
        minute = BaseView.get_valid_input(
            "Minute (0-59)",
            default=dt.minute if dt else None,
            transform=int,
            validate=Validations.validate_minute,
        )

        dt = datetime(year, month, day, hour, minute)

        return dt

    @staticmethod
    def pretty_datetime(dt: datetime | str) -> str:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        day = dt.day
        month_name = dt.strftime("%B")  # Nom du mois en anglais
        year = dt.year
        hour12 = dt.strftime("%I").lstrip("0")  # Heure en 12h, sans zéro devant
        ampm = dt.strftime("%p")  # AM ou PM
        return f"{day} {month_name} {year} @ {hour12}{ampm}"
