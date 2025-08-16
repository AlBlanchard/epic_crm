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
