from typing import Any, Dict, List, Optional

from ..controllers.client_controller import ClientController
from ..controllers.contract_controller import ContractController
from ..controllers.event_controller import EventController

from ..crud.base_crud import AbstractBaseCRUD
from ..controllers.base import AbstractController

from ..utils.app_state import AppState

ENTITY_TO_CONTROLLER = {
    "clients": ClientController,
    "contracts": ContractController,
    "events": EventController,
}

# Permet également de protéger contre les attaques SQL
AUTHORIZED_FILTERS = {
    "clients": [
        {
            "field": "sales_contact_name",
            "name": "Nom du contact commercial",
            "type": "str",
        },
        {"field": "company_name", "name": "Nom de la société", "type": "str"},
        {"field": "is_assigned", "name": "Est assigné", "type": "bool"},
    ],
    "contracts": [
        {"field": "is_signed", "name": "Est signé", "type": "bool"},
        {"field": "is_payed", "name": "Est payé", "type": "bool"},
        {"field": "client_name", "name": "Nom du client", "type": "str"},
        {
            "field": "sales_contact_name",
            "name": "Nom du contact commercial",
            "type": "str",
        },
    ],
    "events": [
        {"field": "is_assigned", "name": "Est assigné", "type": "bool"},
        {
            "field": "support_contact_name",
            "name": "Nom du contact support",
            "type": "str",
        },
    ],
}


class FilterController(AbstractController):
    """Relie la CLI au CRUD et sérialise pour les vues."""

    def _setup_services(self) -> None:
        self.crud = AbstractBaseCRUD(self.session)
        self.app_state = AppState()
        self.controllers = {
            entity: ControllerCls(self.session)
            for entity, ControllerCls in ENTITY_TO_CONTROLLER.items()
        }

    def list_filtered(
        self,
        entity: str,
        filters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Liste les entités filtrées."""

        if entity is None or entity not in ENTITY_TO_CONTROLLER:
            raise ValueError("Entité invalide.")

        # Vérifie les champs de filtre autorisés
        authorized_fields = {f["field"] for f in AUTHORIZED_FILTERS.get(entity, [])}
        for field in filters.keys():
            if field not in authorized_fields:
                raise ValueError(f"Champ de filtre non autorisé : {field}")
        try:
            controller = self.controllers[entity]
            return controller.list_all(filters=filters)
        except Exception as e:
            raise ValueError(
                f"Erreur lors de la récupération des entités filtrées : {e}"
            )
