import click
from ..views.view import BaseView
from ..utils.app_state import AppState
from typing import Any, Dict, List, Optional
from ..views.client_view import ClientView
from ..views.contract_view import ContractView
from ..views.event_view import EventView

ENTITY_TO_VIEW = {
    "clients": ClientView,
    "contracts": ContractView,
    "events": EventView,
}


class FilterView(BaseView):
    def _setup_services(self):
        self.app_state = AppState()
        self.views = {
            entity: ViewCls(session=self.session)
            for entity, ViewCls in ENTITY_TO_VIEW.items()
        }

    def list_filtered(
        self, entity: str, list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Liste les entités filtrées."""

        if entity is None or entity not in ENTITY_TO_VIEW:
            raise ValueError("Entité invalide.")

        try:
            view = self.views[entity]
            return view.list_all(list)
        except Exception as e:
            raise ValueError(
                f"Erreur lors de la récupération des entités filtrées : {e}"
            )

    def choose_filter(
        self, entity: str, authorized_filters: Dict[str, List[Dict[str, str]]]
    ) -> Optional[Dict[str, str]]:
        """
        Affiche les filtres disponibles pour 'entity', demande un numéro,
        puis renvoie le dict du filtre choisi (ex: {"field": "...", "name": "...", "type": "..."}).
        Retourne None si aucun filtre ou si l'utilisateur annule.
        """
        defs: List[Dict[str, str]] = authorized_filters.get(entity, [])

        self._clear_screen()
        if not defs:
            self.console.print(
                "[yellow]Aucun filtre disponible pour cette entité.[/yellow]"
            )
            self.console.print("\n[dim]Appuyez sur Entrée pour revenir...[/dim]")
            self.console.input()
            return None

        # Table simple: id + name
        rows = [{"id": i + 1, "name": d["name"]} for i, d in enumerate(defs)]
        title = f"[cyan]Filtres disponibles — {entity.title()}[/cyan]"
        self._print_table(title, ["id", "name"], rows)

        # Sélection (1..n)
        idx = self.select_id(
            rows=rows, entity="filtre", intro="[dim]Choisissez un filtre...[/dim]"
        )
        if idx is None:
            return None

        # Convertit l'index choisi (1..n) vers l'élément AUTHORIZED_FILTERS
        return defs[int(idx) - 1]

    def enter_filter_criteria(
        self, field_dict: Dict[str, str]
    ) -> Dict[str, Any] | None:
        """
        Demande à l'utilisateur de saisir les critères de filtre pour le champ spécifié.
        """
        if not field_dict:
            return {}

        if field_dict["type"] == "str":
            input = self.get_valid_input(
                f"Entrez la valeur du filtre {field_dict['name']}"
            )
            return {field_dict["field"]: input}

        if field_dict["type"] == "bool":
            input = self.true_or_false(f"{field_dict['name']} ?")
            return {field_dict["field"]: input}
