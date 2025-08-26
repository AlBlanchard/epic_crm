from typing import Any, Optional, Dict, List, Sequence
from sqlalchemy.orm import Session, Query
from abc import ABC


class AbstractBaseCRUD(ABC):
    """Classe de base pour les opérations CRUD génériques."""

    def __init__(self, session: Session):
        self.session = session

    def get_entities(
        self,
        model,
        owner_field: Optional[str] = None,
        owner_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        *,
        eager_options: Sequence = (),  # ex : (selectinload(Client.sales_contact),)
    ) -> List:
        """Récupère des entités avec filtres/tri simples + eager-load optionnel."""
        query: Query = self.session.query(model)

        # Eager load (anti-N+1), si fourni
        if eager_options:
            query = query.options(*eager_options)

        # Whitelist des colonnes disponibles (noms)
        columns = {c.name for c in model.__table__.columns}

        # Filtre "propriétaire"
        if owner_field and owner_id is not None and owner_field in columns:
            query = query.filter(getattr(model, owner_field) == owner_id)

        # Autres filtres (égalité simple)
        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)

        # Pas implémenté car non demandé, peut soulever un pb de sécurité si mal géré
        if order_by:
            raise ValueError("Le tri n'est pas encore implémenté.")

        return query.all()
