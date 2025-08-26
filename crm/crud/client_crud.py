from .base_crud import AbstractBaseCRUD
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.client import Client
from sqlalchemy.orm import selectinload


class ClientCRUD(AbstractBaseCRUD):
    """CRUD operations pour la gestion des clients."""

    def __init__(self, session: Session):
        super().__init__(session)

    # ---------- CREATE ----------
    def create_client(self, client_data: Dict) -> Client:
        """
        Crée un nouveau client.
        Note: La validation des données est faite par le controller.
        """
        try:
            client = Client(**client_data)
            self.session.add(client)
            self.session.commit()
            self.session.refresh(client)
            return client
        except IntegrityError as e:
            self.session.rollback()
            # Relance l'exception pour que le contrôleur puisse la gérer
            raise
        except Exception as e:
            self.session.rollback()
            raise

    # ---------- READ ----------
    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[Client]:
        """Récupère tous les clients avec filtres et tri optionnels, anti-N+1 activé."""
        return self.get_entities(
            Client,
            filters=filters,
            order_by=order_by,
            eager_options=(selectinload(Client.sales_contact),),  # clé anti N+1
        )

    def get_by_id(self, client_id: int) -> Optional[Client]:
        """Récupère un client par son ID."""
        return self.session.get(Client, client_id)

    def get_clients_by_sales_contact(self, sales_contact_id: int) -> List[Client]:
        """Récupère tous les clients assignés à un commercial."""
        return (
            self.session.query(Client)
            .filter_by(sales_contact_id=sales_contact_id)
            .all()
        )

    # ---------- UPDATE ----------
    def update_client(self, client_id: int, client_data: Dict) -> Optional[Client]:
        """
        Met à jour un client existant.
        Note: La validation des données est faite par le controller.
        """
        client = self.session.get(Client, client_id)
        if not client:
            return None

        try:
            for key, value in client_data.items():
                if hasattr(client, key):  # Sécurité basique
                    setattr(client, key, value)

            self.session.commit()
            self.session.refresh(client)
            return client
        except IntegrityError as e:
            self.session.rollback()
            raise
        except Exception as e:
            self.session.rollback()
            raise

    def assign_sales_contact(self, client_id: int, sales_contact_id: int) -> bool:
        """Assigne un commercial à un client."""
        client = self.session.get(Client, client_id)
        if not client:
            return False

        try:
            client.sales_contact_id = sales_contact_id
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise

    # ---------- DELETE ----------
    def delete_client(self, client_id: int) -> bool:
        """
        Supprime un client.
        Note: Les vérifications métier sont faites par le controller.
        """
        client = self.session.get(Client, client_id)
        if not client:
            return False

        try:
            self.session.delete(client)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise

    # -- Utils --

    def client_has_contracts(self, client_id: int) -> bool:
        """Vérifie si un client a des contrats actifs."""
        client = self.session.get(Client, client_id)
        if not client:
            return False
        return client.contracts and any(c.is_active for c in client.contracts)
