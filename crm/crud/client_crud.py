from .base_crud import AbstractBaseCRUD
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.client import Client
from ..models.user import User
from ..models.contract import Contract


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
        self, filters: Optional[Dict[str, Any]] = None, order_by: Optional[str] = None
    ) -> List[Client]:
        """Récupère tous les clients avec filtres et tri optionnels."""
        return self.get_entities(Client, filters=filters, order_by=order_by)

    def get_by_id(self, client_id: int) -> Optional[Client]:
        """Récupère un client par son ID."""
        return self.session.get(Client, client_id)

    def find_by_email(self, email: str) -> Optional[Client]:
        """Trouve un client par son email."""
        return self.session.query(Client).filter_by(email=email).first()

    def find_by_phone(self, phone: str) -> Optional[Client]:
        """Trouve un client par son téléphone."""
        return self.session.query(Client).filter_by(phone=phone).first()

    def find_by_company(self, company_name: str) -> List[Client]:
        """Trouve tous les clients d'une entreprise."""
        return self.session.query(Client).filter_by(company_name=company_name).all()

    def search_by_name(self, name_pattern: str) -> List[Client]:
        """Recherche des clients par nom (pattern)."""
        return (
            self.session.query(Client)
            .filter(Client.full_name.ilike(f"%{name_pattern}%"))
            .all()
        )

    def get_clients_by_sales_contact(self, sales_contact_id: int) -> List[Client]:
        """Récupère tous les clients assignés à un commercial."""
        return (
            self.session.query(Client)
            .filter_by(sales_contact_id=sales_contact_id)
            .all()
        )

    def exists_by_email(self, email: str) -> bool:
        """Vérifie si un client existe avec cet email."""
        return self.session.query(Client).filter_by(email=email).first() is not None

    def exists_by_phone(self, phone: str) -> bool:
        """Vérifie si un client existe avec ce téléphone."""
        return self.session.query(Client).filter_by(phone=phone).first() is not None

    def count_clients(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Compte le nombre de clients avec filtres optionnels."""
        query = self.session.query(Client)
        if filters:
            for key, value in filters.items():
                if hasattr(Client, key):
                    query = query.filter(getattr(Client, key) == value)
        return query.count()

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

    # ---------- CONTRACT MANAGEMENT ----------
    def get_client_contracts(self, client_id: int) -> List[Contract]:
        """Récupère tous les contrats d'un client."""
        return self.session.query(Contract).filter_by(client_id=client_id).all()

    def count_client_contracts(self, client_id: int) -> int:
        """Compte le nombre de contrats d'un client."""
        return self.session.query(Contract).filter_by(client_id=client_id).count()

    def client_has_contracts(self, client_id: int) -> bool:
        """Vérifie si un client a des contrats."""
        return self.count_client_contracts(client_id) > 0

    def get_active_contracts(self, client_id: int) -> List[Contract]:
        """Récupère les contrats actifs d'un client (si vous avez un champ status)."""
        return (
            self.session.query(Contract)
            .filter_by(client_id=client_id)
            .filter(Contract.status == "active")  # Adaptez selon votre modèle
            .all()
        )

    # ---------- SALES CONTACT MANAGEMENT ----------
    def count_clients_by_sales_contact(self, sales_contact_id: int) -> int:
        """Compte le nombre de clients assignés à un commercial."""
        return (
            self.session.query(Client)
            .filter_by(sales_contact_id=sales_contact_id)
            .count()
        )

    def get_sales_contact_workload(self) -> List[Dict[str, Any]]:
        """Récupère la charge de travail de chaque commercial."""
        from sqlalchemy import func

        result = (
            self.session.query(
                User.id, User.username, func.count(Client.id).label("client_count")
            )
            .outerjoin(Client, Client.sales_contact_id == User.id)
            .group_by(User.id, User.username)
            .all()
        )

        return [
            {
                "sales_contact_id": row.id,
                "username": row.username,
                "client_count": row.client_count,
            }
            for row in result
        ]

    # ---------- UTILITY METHODS ----------
    def client_exists_by_id(self, client_id: int) -> bool:
        """Vérifie si un client existe par son ID."""
        return self.session.get(Client, client_id) is not None

    def get_client_stats(self, client_id: int) -> Dict[str, Any]:
        """Récupère les statistiques d'un client."""
        client = self.session.get(Client, client_id)
        if not client:
            return {}

        contract_count = self.count_client_contracts(client_id)

        return {
            "client_id": client_id,
            "full_name": client.full_name,
            "email": client.email,
            "company_name": client.company_name,
            "sales_contact_id": client.sales_contact_id,
            "contract_count": contract_count,
            "has_contracts": contract_count > 0,
            "created_at": getattr(client, "created_at", None),
            "updated_at": getattr(client, "updated_at", None),
        }

    def get_clients_by_company_stats(self) -> List[Dict[str, Any]]:
        """Récupère les statistiques par entreprise."""
        from sqlalchemy import func

        result = (
            self.session.query(
                Client.company_name,
                func.count(Client.id).label("client_count"),
                func.count(Contract.id).label("contract_count"),
            )
            .outerjoin(Contract, Contract.client_id == Client.id)
            .group_by(Client.company_name)
            .all()
        )

        return [
            {
                "company_name": row.company_name,
                "client_count": row.client_count,
                "contract_count": row.contract_count,
            }
            for row in result
        ]

    def search_clients(self, search_term: str) -> List[Client]:
        """Recherche globale sur les clients (nom, email, entreprise)."""
        search_pattern = f"%{search_term}%"
        return (
            self.session.query(Client)
            .filter(
                (Client.full_name.ilike(search_pattern))
                | (Client.email.ilike(search_pattern))
                | (Client.company_name.ilike(search_pattern))
            )
            .all()
        )
