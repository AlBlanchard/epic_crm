from typing import Iterable, TypeVar


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
