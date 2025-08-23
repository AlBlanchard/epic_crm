import calendar
from typing import Iterable, TypeVar
from datetime import datetime


class Validations:

    @staticmethod
    def validate_user_id(user_id: str, valid_ids: list[str]) -> bool:
        if user_id not in valid_ids:
            raise ValueError("ID utilisateur invalide.")
        return True

    @staticmethod
    def validate_email(email: str) -> bool:
        if "@" not in email:
            raise ValueError("Email invalide.")
        return True

    @staticmethod
    def validate_number(number: str):
        if not number.isdigit():
            raise ValueError("Le numéro doit être un entier.")

    @staticmethod
    def is_in_list(value: str, list: Iterable[str]) -> bool:
        if value not in list:
            raise ValueError(f"{value} n'existe pas. Veuillez réessayer.")
        return True

    @staticmethod
    def not_empty(value: str) -> bool:
        if not value.strip():
            raise ValueError("Ce champ ne peut pas être vide.")
        if value.strip() == "":
            raise ValueError("Ce champ ne peut pas être vide.")
        return True

    @staticmethod
    def confirm_action(prompt: str) -> bool:
        response = input(f"{prompt} (o/n) : ").strip().lower()
        if response == "o":
            return True
        elif response == "n":
            return False
        else:
            raise ValueError("Réponse invalide. Veuillez répondre par 'o' ou 'n'.")

    @staticmethod
    def validate_year(year: int) -> None:
        current = datetime.now().year
        if year < current:
            raise ValueError(f"L'année doit être ≥ {current}.")

    @staticmethod
    def validate_month(month: int) -> None:
        if not (1 <= month <= 12):
            raise ValueError("Le mois doit être compris entre 1 et 12.")

    @staticmethod
    def validate_day_in_month(day: int, month: int, year: int) -> None:
        if not (1 <= day <= 31):
            raise ValueError("Le jour doit être compris entre 1 et 31.")
        _, max_day = calendar.monthrange(year, month)
        if day > max_day:
            raise ValueError(f"Le mois {month}/{year} a {max_day} jours (pas {day}).")

    @staticmethod
    def validate_hour(hour: int) -> None:
        if not (0 <= hour <= 23):
            raise ValueError("L'heure doit être comprise entre 0 et 23.")

    @staticmethod
    def validate_minute(minute: int) -> None:
        if not (0 <= minute <= 59):
            raise ValueError("La minute doit être comprise entre 0 et 59.")

    @staticmethod
    def validate_future_datetime(dt: datetime) -> None:
        """Vérifie que la date/heure est dans le futur (pas de dates passées)."""
        now = datetime.now()
        if dt < now:
            raise ValueError("La date/heure doit être dans le futur.")

    @staticmethod
    def validate_date_order(start_date: datetime, end_date: datetime) -> None:
        """Vérifie que la date de fin est postérieure à la date de début."""
        if end_date <= start_date:
            raise ValueError(
                f"La date de fin ({end_date}) doit être postérieure à la date de début ({start_date})."
            )
