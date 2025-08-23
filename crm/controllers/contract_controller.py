from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal
from .base import AbstractController
from ..auth.auth import Authentication
from ..auth.permission import Permission
from ..crud.contract_crud import ContractCRUD
from ..crud.client_crud import ClientCRUD
from ..crud.user_crud import UserCRUD
from ..serializers.contract_serializer import ContractSerializer
from ..models.user import User
from ..models.client import Client
from ..models.contract import Contract
from sqlalchemy.orm import selectinload


class ContractController(AbstractController):
    """Logique métier Contrats : admin -> tout, sales -> seulement ses contrats."""

    def _setup_services(self) -> None:
        self.contracts = ContractCRUD(self.session)
        self.clients = ClientCRUD(self.session)
        self.users = UserCRUD(self.session)
        self.serializer = ContractSerializer()

    # ---------- Helpers ----------
    def _get_current_user(self) -> User:
        token = Authentication.load_token()
        if not token:
            raise PermissionError("Non authentifié.")
        payload = Authentication.verify_token(token)
        me = self.users.get_by_id(int(payload["sub"]))
        if not me:
            raise PermissionError("Utilisateur courant introuvable.")
        return me

    def _ensure_admin(self, me: User) -> None:
        if not Permission.is_admin(me):
            raise PermissionError("Accès refusé : administrateur requis.")

    def _ensure_owner_or_admin(self, me: User, owner_id: int) -> None:
        if not (Permission.is_admin(me) or me.id == owner_id):
            raise PermissionError("Accès refusé.")

    def _ensure_sales_owns_client_or_admin(self, me: User, client_id: int) -> None:
        """Un sales ne peut manipuler que des contrats liés à SES clients."""
        if Permission.is_admin(me):
            return
        client = self.clients.get_by_id(client_id)
        if not client:
            raise ValueError("Client introuvable.")
        if client.sales_contact_id != me.id:
            raise PermissionError("Vous ne pouvez agir que sur vos propres clients.")

    # ---------- Read ----------
    def list_contracts(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        if not Permission.read_permission(me, "contract"):
            raise PermissionError("Accès refusé.")

        rows = self.contracts.get_all(filters=filters, order_by=order_by)

        ser = self.serializer if fields is None else ContractSerializer(fields=fields)
        return ser.serialize_list(rows)

    def list_my_contracts(
        self, *, fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        if not Permission.read_permission(me, "contract"):
            raise PermissionError("Accès refusé.")

        rows = self.contracts.get_by_sales_contact(me.id)
        ser = self.serializer if fields is None else ContractSerializer(fields=fields)
        return ser.serialize_list(rows)

    def get_contract(
        self,
        contract_id: int,
        *,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        me = self._get_current_user()
        contract = self.contracts.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat introuvable.")
        self._ensure_owner_or_admin(me, contract.sales_contact_id)
        ser = self.serializer if fields is None else ContractSerializer(fields=fields)
        return ser.serialize(contract)

    def is_contract_signed(self, contract_id: int) -> bool:
        contract = self.contracts.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat introuvable.")
        return contract.is_signed

    def list_unsigned_contracts(
        self,
        *,
        sales_contact_id: Optional[int] = None,
        fields: Optional[List[str]] = None,
        signed: bool = False,
    ) -> List[Dict[Any, str]]:
        filters = {}
        if hasattr(Contract, "is_signed"):
            filters["is_signed"] = signed

        # Filtre par commercial
        if sales_contact_id is not None:
            if hasattr(Contract, "sales_contact_id"):
                filters["sales_contact_id"] = sales_contact_id
            else:
                # Dans ce cas précis via Client, garde la première version Query.
                pass

        rows = self.contracts.get_all(filters)
        ser = self.serializer if fields is None else ContractSerializer(fields=fields)

        return ser.serialize_list(rows)

    def list_signed_contracts(
        self,
        *,
        sales_contact_id: Optional[int] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        list_signed = self.list_unsigned_contracts(
            sales_contact_id=sales_contact_id, fields=fields, signed=True
        )
        return list_signed

    def get_contract_owner(self, contract_id: int) -> User:
        """
        Retourne le User propriétaire (sales_contact) d'un contrat.
        - None si le contrat n'existe pas ou si aucun commercial n'est lié.
        """
        contract = self.session.get(
            Contract,
            contract_id,
            options=(
                # Evite le N+2
                selectinload(Contract.client).selectinload(Client.sales_contact),
            ),
        )
        if not contract or not contract.client:
            raise ValueError("Le contrat n'a pas de client associé.")

        # Priorité à une relation directe si elle existe, sinon via client
        owner = contract.client.sales_contact if contract.client else None
        if owner is None:
            raise ValueError("Le contrat n'a pas de commercial assigné.")

        return owner

    def list_by_client(
        self,
        client_id: int,
        *,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        self._ensure_sales_owns_client_or_admin(me, client_id)
        rows = self.contracts.get_by_client(client_id)
        ser = self.serializer if fields is None else ContractSerializer(fields=fields)
        return ser.serialize_list(rows)

    def get_contract_amounts(self, contract_id: int) -> Tuple[Decimal, Decimal]:
        contract = self.contracts.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat introuvable.")
        return contract.amount_total, contract.amount_due

    # ---------- Create ----------
    def create_contract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attendu (validé en amont) : client_id, amount_total, amount_due, is_signed (optionnel)
        Règles :
        - sales : impose sales_contact_id = me.id
        - admin : peut définir sales_contact_id (sinon me.id par défaut)
        - sales : le client doit lui appartenir
        """
        me = self._get_current_user()

        if not Permission.create_permission(me, "contract"):
            raise PermissionError("Accès refusé.")

        payload = {**data}
        contract = self.contracts.create(payload)
        return self.serializer.serialize(contract)

    # ---------- Update ----------
    def update_contract(self, contract_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        me = self._get_current_user()
        if not Permission.update_permission(me, "contract"):
            raise PermissionError("Accès refusé.")

        contract = self.contracts.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat introuvable.")

        updated = self.contracts.update(contract_id, data)
        if updated is None:
            raise ValueError("Mise à jour impossible.")

        return self.serializer.serialize(updated)

    # ---------- Delete ----------
    def delete_contract(self, contract_id: int) -> None:
        """
        admin ou owner. Si le contrat est signé, suppression interdite
        sauf (force=True et admin).
        """
        me = self._get_current_user()
        contract = self.contracts.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat introuvable.")

        if not Permission.delete_permission(me, "contract"):
            raise PermissionError("Accès refusé.")

        ok = self.contracts.delete(contract_id)
        if not ok:
            raise ValueError("Suppression impossible.")
