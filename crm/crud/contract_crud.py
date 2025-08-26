from .base_crud import AbstractBaseCRUD
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from ..models.contract import Contract
from ..models.client import Client


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
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
    ) -> List[Contract]:
        """Récupère tous les contrats avec filtres/tri et eager-load anti-N+1."""
        return self.get_entities(
            Contract,
            filters=filters,
            order_by=order_by,
            eager_options=(
                # N+1
                selectinload(Contract.client),
                # N+2
                selectinload(Contract.client).selectinload(Client.sales_contact),
            ),
        )

    def get_by_id(self, contract_id: int) -> Optional[Contract]:
        """Récupère un contrat par son ID."""
        return self.session.get(Contract, contract_id)

    def get_by_client(self, client_id: int) -> List[Contract]:
        """Récupère les contrats d'un client."""
        return self.session.query(Contract).filter_by(client_id=client_id).all()

    def get_by_sales_contact(self, sales_contact_id: int) -> List[Contract]:
        """Récupère tous les contrats liés à un commercial donné."""
        return (
            self.session.query(Contract)
            .options(selectinload(Contract.client).selectinload(Client.sales_contact))
            .filter(Contract.client.sales_contact_id == sales_contact_id)
            .all()
        )

    def get_unsigned_contracts(
        self, *, sales_contact_id: Optional[int] = None, **kw
    ) -> List[Contract]:
        filters = {}
        if hasattr(Contract, "is_signed"):
            filters["is_signed"] = False

        eager = (selectinload(Contract.client).selectinload(Client.sales_contact),)

        # Filtre par commercial
        if sales_contact_id is not None:
            if hasattr(Contract, "sales_contact_id"):
                filters["sales_contact_id"] = sales_contact_id
            else:
                # Dans ce cas précis (via Client), garde la première version Query.
                pass

        return self.get_all(filters=filters, **kw)

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
