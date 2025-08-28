import sys
import click
import platform
import os
from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Callable,
    TypeVar,
    Mapping,
    Union,
    Tuple,
)
from sqlalchemy.orm import Session
from ..database import SessionLocal
from rich.table import Table
from rich.console import Console
from ..errors.exceptions import UserCancelledInput
from ..utils.app_state import AppState
from ..utils.validations import Validations
from ..utils.pretty import Pretty
from getpass import getpass
from datetime import datetime

ColumnSpec = Union[str, Tuple[str, str]]

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
        self.valid = Validations()

    @abstractmethod
    def _setup_services(self) -> None:
        """Initialise les services spécifiques de la view."""
        pass

    @staticmethod
    def _clear_screen():
        """Efface le contenu de la console."""

        user_platform = platform.system().lower()

        if user_platform == "windows":
            os.system("cls")
        else:
            os.system("clear")

    def _print_back_choice(self) -> None:
        self.console.print(
            "[italic yellow dim]CTRL+C ou entrer 'q' pour annuler.[/italic yellow dim]"
        )

    def _print_table(
        self, title: str, columns: List[ColumnSpec], rows: List[Dict[str, Any]]
    ) -> None:
        """
        columns:
        - "client_name"  -> header "client_name"
        - ("client_name", "Client") -> header "Client"
        """
        table = Table(title=title, show_lines=True)

        # Prépare key, header pour toutes les colonnes
        normalized: List[Tuple[str, str]] = []
        for col in columns:
            if isinstance(col, tuple):
                key, header = col
            else:
                key, header = col, col
            normalized.append((key, header))
            table.add_column(header, overflow="fold")

        for r in rows:
            table.add_row(*[str(r.get(key, "")) for key, _ in normalized])

        self.console.print(table)

    def true_or_false(self, prompt: str) -> bool:
        response = input(f"{prompt} (o/n) : ").strip().lower()
        if response == "o":
            return True
        elif response == "n":
            return False
        elif response == "":
            return False
        else:
            raise ValueError("Réponse invalide. Veuillez répondre par 'o' ou 'n'.")

    # ---------- Input ----------
    # Cette grosse methode permet de recuperer une entree utilisateur valide
    # Pas mal de paramètre pour gérer les différentes situations
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
    ) -> T | None:
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
                    AppState.set_neutral_message("Action annulée par l'utilisateur.")
                    return None

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

    # ---------- Date Input --------
    # Afin de renseigner une date facilement
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
            default_date_str = Pretty.pretty_datetime(dt)
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

    # ---------- Tables ----------
    def select_id(
        self,
        *,
        rows: Iterable[Mapping],
        entity: str,
        intro: Optional[str] = None,
        id_label: Optional[str] = None,
    ) -> Optional[str]:
        """
        Sous fonction pour sélectionner un ID parmi les rows d'un tableau.

        Params
        ------
        rows : Iterable[Mapping]
            Les éléments affichés ailleurs (on ne les affiche pas ici), chacun doit avoir 'id'.
        entity : str
            Nom de l'entité pour le texte (ex: 'utilisateur', 'client', 'contrat', 'événement').
        intro : Optional[str]
            Ligne d'introduction au-dessus du prompt (ex: "[dim]Sélectionnez un client...[/dim]").
            Défaut: f"[dim]Sélectionnez un {entity}...[/dim]"
        id_label : Optional[str]
            Libellé du champ d'entrée (ex: "ID du client").
            Défaut: f"ID du {entity}"

        Returns
        -------
        Optional[int]
            L'ID saisi (int). Retourne None si `selector` est False.
        """
        validate_number = Validations.validate_number

        # Texte d'intro
        line = intro if intro is not None else f"[dim]Sélectionnez un {entity}...[/dim]"
        self.console.print(line)
        self._print_back_choice()

        # Construit la liste des ids autorisés (tout en str)
        try:
            allowed_ids = [str(item["id"]) for item in rows]
        except Exception:
            # Si jamais 'rows' contient des objets avec attribut .id plutôt que des dicts
            allowed_ids = [str(getattr(item, "id")) for item in rows]

        # Libellé du champ
        label = id_label if id_label is not None else f"ID du {entity}"

        # Lecture sécurisée + validation + appartenance à la liste
        str_id = self.get_valid_input(
            label,
            validate=validate_number,
            list_to_compare=allowed_ids,
        )

        return str_id

    def list_entities(
        self,
        *,
        rows: List[Dict[str, Any]],
        title: str,
        columns: List[ColumnSpec],
        selector: bool = False,
        has_filter: bool = False,
        entity: Optional[str] = None,  # "utilisateur", "client", etc...
        prompt: Optional[str] = None,  # ex: "[dim]Sélectionnez un utilisateur...[/dim]"
    ) -> Optional[int | bool]:
        """
        Affiche un tableau générique avec entêtes custom et gère la sélection d'ID facultative.
        - `columns` accepte "key" ou ("key", "Header")
        - aucune transformation/formatage ici : prépare `rows` en amont si nécessaire.
        """
        self._clear_screen()

        self._print_table(title, columns, rows)

        if selector:
            ent = entity or "élément"
            pr = prompt or f"[dim]Sélectionnez un {ent}...[/dim]"
            selected_id = self.select_id(rows=rows, entity=ent, intro=pr)
            if selected_id is not None:
                return int(selected_id)
            return None


        if has_filter:
            return self.true_or_false("Souhaitez vous appliquer un filtre ?")

        self.console.print("\n[dim]Appuyez sur Entrée pour revenir au menu...[/dim]")
        AppState.display_error_or_success_message()
        self.console.input()
        return None
