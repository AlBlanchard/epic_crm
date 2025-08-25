import textwrap
from datetime import datetime
from typing import List


class Pretty:
    """Classe pour la mise en forme des chaînes de caractères."""

    @staticmethod
    def pretty_datetime(dt: datetime | str) -> str:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        day = dt.day
        month_name = dt.strftime("%B")  # Nom du mois en anglais
        year = dt.year
        hour12 = dt.strftime("%I").lstrip("0")  # Heure en 12h, sans zéro devant
        ampm = dt.strftime("%p")  # AM ou PM
        minute = dt.strftime("%M")  # Minute avec zéro devant si besoin
        return f"{day} {month_name} {year} @ {hour12}:{minute} {ampm}"

    @staticmethod
    def pretty_email(email: str) -> str:
        if not email:
            return "Aucun"
        return f"[underline blue]{email}[/underline blue]"

    @staticmethod
    def pretty_currency(currency: float, debt: bool = False) -> str:
        if debt and currency > 0:
            return f"[red]{currency:.2f} €[/red]"
        return f"[green]{currency:.2f} €[/green]"

    @staticmethod
    def pretty_bool(value: bool) -> str:
        return "[cyan]Oui[/cyan]" if value else "[red]Non[/red]"

    @staticmethod
    def pretty_contact(contacts: List[str]) -> str:
        if not contacts:
            return "Aucun"
        if contacts == []:
            return "Aucun"

        pretty_contacts = []

        for contact in contacts:
            if "@" in contact:
                contact = f"{Pretty.pretty_email(contact)}"
            pretty_contacts.append(contact)

        out = "\n".join(contact for contact in pretty_contacts)

        return out

    @staticmethod
    def pretty_notes(notes: List[str], width: int = 60, prefix: str = "-> ") -> str:
        """
        Transforme une liste de notes en une chaîne prête pour l'affichage dans un tableau Rich :
        - chaque note est préfixée par 'prefix'
        - les notes trop longues sont wrap à 'width' caractères, sans couper les mots
        - les lignes suivantes sont alignées (espaces à la place de la flèche)
        """
        if not notes:
            return "Aucune"

        indent = " " * len(prefix)
        blocks: list[str] = []
        for n in notes:
            if not n:
                continue
            wrapped = textwrap.fill(
                n.strip(),
                width=width,
                initial_indent=prefix,
                subsequent_indent=indent,
                break_long_words=False,
                break_on_hyphens=True,
            )
            blocks.append(wrapped)

        return "\n".join(blocks) if blocks else "Aucune"

    @staticmethod
    def pretty_roles(roles: list[str]):
        if not roles:
            return "Aucun"
        return ", ".join(role.capitalize() for role in roles)
