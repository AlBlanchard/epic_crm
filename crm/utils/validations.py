import calendar
import re
from decimal import Decimal, InvalidOperation
from typing import Iterable, TypeVar
from datetime import datetime


class Validations:
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    PHONE_REGEX = r"^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$"

    @staticmethod
    def validate_user_id(user_id: str, valid_ids: list[str]) -> bool:
        if user_id not in valid_ids:
            raise ValueError("ID utilisateur invalide.")
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

    @staticmethod
    def validate_str_max_length(value: str, max_length: int = 100) -> None:
        """Vérifie que la chaîne ne dépasse pas une longueur maximale."""
        if value is not None and isinstance(value, str):
            if len(value) > max_length:
                raise ValueError(
                    f"La chaîne ne doit pas dépasser {max_length} caractères."
                )
        else:
            raise ValueError("La valeur doit être une chaîne.")

    @staticmethod
    def validate_email(email: str) -> None:
        """Vérifie que l'email est valide."""
        Validations.validate_str_max_length(email, max_length=254)
        if not Validations.EMAIL_REGEX.match(email):
            raise ValueError("Email invalide.")

    @staticmethod
    def validate_int_max_length(value: int | str | None, max_length: int = 10) -> None:
        """Vérifie que l'entier ne dépasse pas une longueur maximale."""
        if value is None:
            raise ValueError("La valeur ne peut pas être nulle.")
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValueError("La valeur doit être un entier.")

        if not isinstance(int_value, int):
            raise ValueError("La valeur doit être un entier.")
        if int_value > 10**max_length - 1:
            raise ValueError(f"L'entier ne doit pas dépasser {max_length} chiffres.")

    @staticmethod
    def validate_phone(phone: str) -> None:
        if len(phone) > 15:
            raise ValueError(
                "Le numéro de téléphone ne doit pas dépasser 15 caractères."
            )
        if phone and not re.match(Validations.PHONE_REGEX, phone):
            raise ValueError("Le numéro de téléphone est invalide.")

    @staticmethod
    def validate_currency(value) -> None:
        """
        Vérifie que la valeur est un nombre avec au maximum 2 décimales.
        Retourne un Decimal si OK, lève ValueError sinon.
        """
        try:
            d = Decimal(str(value))
        except (InvalidOperation, ValueError):
            raise ValueError(f"Valeur invalide pour une devise : {value}")

        if d != d.quantize(Decimal("0.01")):
            raise ValueError(f"Le montant {value} doit avoir au maximum 2 décimales.")

    @staticmethod
    def validate_positive_integer(value: int | str, max_length: int = 6) -> None:
        try:
            int_value = int(value)
        except Exception as e:
            raise ValueError("La valeur doit être un entier.")
        if int_value <= 0:
            raise ValueError("La valeur doit être un entier positif.")
        Validations.validate_int_max_length(int_value, max_length)
