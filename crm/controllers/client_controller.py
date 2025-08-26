from typing import Dict, Any, Optional, List
from .base import AbstractController
from ..auth.permission import Permission
from ..crud.client_crud import ClientCRUD
from ..crud.user_crud import UserCRUD
from ..serializers.client_serializer import ClientSerializer
from ..models.user import User


class ClientController(AbstractController):

    def _setup_services(self) -> None:
        self.clients = ClientCRUD(self.session)
        self.users = UserCRUD(self.session)
        self.serializer = ClientSerializer()

    # ---------- Read ----------
    def list_all(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:

        me = self._get_current_user()
        if not Permission.read_permission(me, "client"):
            raise PermissionError("Accès refusé.")

        rows = self.clients.get_all(filters=filters, order_by=order_by)

        ser = self.serializer if fields is None else ClientSerializer(fields=fields)
        return ser.serialize_list(rows)

    def list_my_clients(
        self,
        *,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:

        me = self._get_current_user()
        if not Permission.read_permission(me, "client"):
            raise PermissionError("Accès refusé.")

        rows = self.clients.get_clients_by_sales_contact(me.id)
        ser = self.serializer if fields is None else ClientSerializer(fields=fields)
        return ser.serialize_list(rows)

    def get_client(
        self,
        client_id: int,
        *,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        me = self._get_current_user()
        client = self.clients.get_by_id(client_id)
        if not client:
            raise ValueError("Client introuvable.")
        self._ensure_owner_or_admin(me, client.sales_contact_id)
        ser = self.serializer if fields is None else ClientSerializer(fields=fields)
        return ser.serialize(client)

    def get_owner(self, client_id: int) -> User:
        client = self.clients.get_by_id(client_id)
        if not client:
            raise ValueError("Client introuvable.")
        return self.users.get_by_id(client.sales_contact_id)

    # ---------- Create ----------
    def create_client(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        sales/admin :
          - sales peut créer un client ; par défaut, on force sales_contact_id = me.id
          - seul admin peut créer pour un autre commercial (sales_contact_id différent)
        """
        me = self._get_current_user()

        if not Permission.create_permission(me, "client"):
            raise PermissionError("Accès refusé.")

        # si pas fourni, on assigne à soi-même
        sales_contact_id = data.get("sales_contact_id", me.id)

        if not Permission.is_admin(me) and sales_contact_id != me.id:
            raise PermissionError(
                "Seul un administrateur peut assigner à un autre commercial."
            )

        payload = {**data, "sales_contact_id": sales_contact_id}
        client = self.clients.create_client(payload)
        return self.serializer.serialize(client)

    # ---------- Update ----------
    def update_client(self, client_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        admin ou owner :
          - owner peut modifier ses champs
          - assigner à un autre commercial => admin-only
        """
        me = self._get_current_user()
        client = self.clients.get_by_id(client_id)
        if not client:
            raise ValueError("Client introuvable.")

        self._ensure_owner_or_admin(me, client.sales_contact_id)

        # empêcher un non-admin de transférer le client à quelqu'un d'autre
        if "sales_contact_id" in data and not Permission.is_admin(me):
            if data["sales_contact_id"] != me.id:
                raise PermissionError(
                    "Seul un administrateur peut réassigner le client."
                )

        updated = self.clients.update_client(client_id, data)
        if updated is None:
            raise ValueError("Mise à jour impossible.")
        return self.serializer.serialize(updated)

    # ---------- Delete ----------
    def delete_client(self, client_id: int, *, force: bool = False) -> None:
        """
        admin ou owner :
          - refuse si le client a des contrats (sauf force=True et admin)
        """
        me = self._get_current_user()
        client = self.clients.get_by_id(client_id)
        if not client:
            raise ValueError("Client introuvable.")

        self._ensure_owner_or_admin(me, client.sales_contact_id)

        if self.clients.client_has_contracts(client_id):
            if not (force and Permission.is_admin(me)):
                raise PermissionError(
                    "Le client a des contrats. Suppression interdite."
                )

        ok = self.clients.delete_client(client_id)
        if not ok:
            raise ValueError("Suppression impossible.")

    # ---------- Assignation ----------
    def assign_sales_contact(
        self, client_id: int, sales_contact_id: int
    ) -> Dict[str, Any]:
        """
        admin-only : réassigner un client à un autre commercial
        """
        me = self._get_current_user()
        self._ensure_admin(me)

        ok = self.clients.assign_sales_contact(client_id, sales_contact_id)
        if not ok:
            raise ValueError("Assignation impossible (client inexistant ?).")
        client = self.clients.get_by_id(client_id)
        return self.serializer.serialize(client)
