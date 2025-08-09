from typing import Optional, Type, Dict, Callable, List
from sqlalchemy.orm import Session
from abc import ABC


class AbstractBaseCRUD(ABC):
    """Classe de base pour les opérations CRUD génériques."""

    def __init__(self, session: Session):
        self.session = session

    def get_entities(
        self,
        model: Type,
        owner_field: Optional[str] = None,
        owner_id: Optional[int] = None,
        filters: Optional[Dict] = None,
        order_by: Optional[str] = None,
    ) -> List:
        """
        Récupère des entités avec filtres facultatifs.

        Args:
            model (Type): La classe SQLAlchemy (Client, Contract, etc.)
            owner_field (str, optional): Le champ représentant le propriétaire (ex: "sales_contact_id")
            owner_id (int, optional): L'ID du propriétaire pour filtrer (à passer depuis le controller)
            filters (dict, optional): Autres filtres {champ: valeur}
            order_by (str, optional): Champ de tri

        Returns:
            list: Liste des objets correspondant aux critères.
        """
        query = self.session.query(model)

        # Filtrage par propriétaire
        if owner_field and owner_id is not None:
            query = query.filter(getattr(model, owner_field) == owner_id)

        # Autres filtres
        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)

        # Tri
        if order_by and hasattr(model, order_by):
            query = query.order_by(getattr(model, order_by))

        return query.all()
