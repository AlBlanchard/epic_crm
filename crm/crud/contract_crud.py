from .base_crud import AbstractBaseCRUD
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..models.contract import Contract


class ContractCRUD(AbstractBaseCRUD):
    """CRUD operations basiques pour les contrats."""

    def __init__(self, session: Session):
        super().__init__(session)

    # ---------- CREATE ----------
    def create(self, contract_data: Dict) -> Contract:
        """Crée un nouveau contrat."""
        try:
            contract = Contract(**contract_data)
            self.session.add(contract)
            self.session.commit()
            self.session.refresh(contract)
            return contract
        except IntegrityError:
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            raise

    # ---------- READ ----------
    def get_all(
        self, filters: Optional[Dict[str, Any]] = None, order_by: Optional[str] = None
    ) -> List[Contract]:
        """Récupère tous les contrats avec filtres optionnels."""
        return self.get_entities(Contract, filters=filters, order_by=order_by)

    def get_by_id(self, contract_id: int) -> Optional[Contract]:
        """Récupère un contrat par son ID."""
        return self.session.get(Contract, contract_id)

    def get_by_client(self, client_id: int) -> List[Contract]:
        """Récupère les contrats d'un client."""
        return self.session.query(Contract).filter_by(client_id=client_id).all()

    def get_by_sales_contact(self, sales_contact_id: int) -> List[Contract]:
        """Récupère les contrats d'un commercial."""
        return (
            self.session.query(Contract)
            .filter_by(sales_contact_id=sales_contact_id)
            .all()
        )

    # ---------- UPDATE ----------
    def update(self, contract_id: int, contract_data: Dict) -> Optional[Contract]:
        """Met à jour un contrat."""
        contract = self.session.get(Contract, contract_id)
        if not contract:
            return None

        try:
            for key, value in contract_data.items():
                if hasattr(contract, key):
                    setattr(contract, key, value)
            self.session.commit()
            self.session.refresh(contract)
            return contract
        except IntegrityError:
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            raise

    # ---------- DELETE ----------
    def delete(self, contract_id: int) -> bool:
        """Supprime un contrat."""
        contract = self.session.get(Contract, contract_id)
        if not contract:
            return False

        try:
            self.session.delete(contract)
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            raise

    # ---------- UTILITY ----------
    def exists(self, contract_id: int) -> bool:
        """Vérifie si un contrat existe."""
        return self.session.get(Contract, contract_id) is not None

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Compte les contrats avec filtres optionnels."""
        query = self.session.query(Contract)
        if filters:
            for key, value in filters.items():
                if hasattr(Contract, key):
                    query = query.filter(getattr(Contract, key) == value)
        return query.count()
