from typing import Dict, Any, Optional, List
from .base import AbstractController
from ..auth.auth import Authentication
from ..auth.permission import Permission
from ..crud.contract_crud import ContractCRUD
from ..crud.client_crud import ClientCRUD
from ..crud.user_crud import UserCRUD
from ..serializers.contract_serializer import ContractSerializer
from ..models.user import User


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
        if Permission.is_admin(me):
            rows = self.contracts.get_all(filters=filters, order_by=order_by)
        else:
            rows = self.contracts.get_by_sales_contact(me.id)
        ser = self.serializer if fields is None else ContractSerializer(fields=fields)
        return ser.serialize_list(rows)

    def list_my_contracts(
        self, *, fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()
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

        client_id = data.get("client_id")
        if client_id is None:
            raise ValueError("client_id requis.")
        self._ensure_sales_owns_client_or_admin(me, int(client_id))

        sales_contact_id = data.get("sales_contact_id", me.id)
        if not Permission.is_admin(me) and sales_contact_id != me.id:
            raise PermissionError("Assignation à un autre commercial interdite.")

        payload = {**data, "sales_contact_id": sales_contact_id}
        contract = self.contracts.create(payload)
        return self.serializer.serialize(contract)

    # ---------- Update ----------
    def update_contract(self, contract_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        admin ou owner :
        - changer client_id ou sales_contact_id => admin-only
        """
        me = self._get_current_user()
        contract = self.contracts.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat introuvable.")

        self._ensure_owner_or_admin(me, contract.sales_contact_id)

        # verrou pour champs sensibles si non-admin
        if not Permission.is_admin(me):
            forbidden = {"client_id", "sales_contact_id"}
            data = {k: v for k, v in data.items() if k not in forbidden}

        # si admin change client_id → vérifier existence du client
        if "client_id" in data and Permission.is_admin(me):
            cid = int(data["client_id"])
            if not self.clients.client_exists_by_id(cid):
                raise ValueError("Nouveau client introuvable.")

        updated = self.contracts.update(contract_id, data)
        if updated is None:
            raise ValueError("Mise à jour impossible.")
        return self.serializer.serialize(updated)

    def mark_signed(self, contract_id: int, is_signed: bool = True) -> Dict[str, Any]:
        """Owner ou admin peuvent (dé)marquer le contrat comme signé."""
        me = self._get_current_user()
        contract = self.contracts.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat introuvable.")
        self._ensure_owner_or_admin(me, contract.sales_contact_id)

        updated = self.contracts.update(contract_id, {"is_signed": bool(is_signed)})
        if updated is None:
            raise ValueError("Mise à jour impossible.")
        return self.serializer.serialize(updated)

    # ---------- Delete ----------
    def delete_contract(self, contract_id: int, *, force: bool = False) -> None:
        """
        admin ou owner. Si le contrat est signé, suppression interdite
        sauf (force=True et admin).
        """
        me = self._get_current_user()
        contract = self.contracts.get_by_id(contract_id)
        if not contract:
            raise ValueError("Contrat introuvable.")

        self._ensure_owner_or_admin(me, contract.sales_contact_id)

        if contract.is_signed and not (force and Permission.is_admin(me)):
            raise PermissionError(
                "Contrat signé : suppression interdite (admin peut forcer)."
            )

        ok = self.contracts.delete(contract_id)
        if not ok:
            raise ValueError("Suppression impossible.")
