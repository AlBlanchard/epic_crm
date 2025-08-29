import click
from .view import BaseView
from ..utils.app_state import AppState


class MenuView(BaseView):
    def _setup_services(self) -> None:
        self.app_state = AppState()

    def run_menu(self, title: str, items: list[str], logout: bool = False) -> str | int:
        """
        Affiche un menu et retourne la clé choisie.
        items: liste de labels (les numéros sont ajoutés automatiquement)
        Retourne "0", "R", ou l'index choisi en str.
        """
        while True:
            self._clear_screen()
            self.console.print(f"\n[bold cyan]{title}[/bold cyan]")

            # Affichages des options
            for i, label in enumerate(items, start=1):
                self.console.print(f"{i}. {label}")

            # Affichage de l'option de retour ou déconnexion
            if logout:
                self.console.print("\n[yellow]R. Se déconnecter[/yellow]")
            else:
                self.console.print("\n[yellow]R. Retour[/yellow]")

            self.print_quit_option()

            self.app_state.display_error_or_success_message()

            raw = click.prompt("\nChoix", type=str).strip().upper()

            if raw in {"0", "R"} or raw.isdigit():
                if raw == "0":
                    self.view_exit()
                    return "0"

                if raw == "R":
                    if logout:
                        self.view_logout()
                        return "R"
                    return "R"

                if 0 < int(raw) <= len(items):
                    return int(raw)

            self.app_state.set_error_message("[red]Choix invalide[/red]")
