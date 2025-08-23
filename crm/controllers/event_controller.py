from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import AbstractController
from ..auth.auth import Authentication
from ..auth.permission import Permission
from ..crud.event_crud import EventCRUD
from ..crud.contract_crud import ContractCRUD
from ..crud.user_crud import UserCRUD
from ..serializers.event_serializer import EventSerializer
from ..models.user import User
from ..utils.validations import Validations


class EventController(AbstractController):
    """Logique métier Événements : admin -> tout, support -> ses événements."""

    def _setup_services(self) -> None:
        self.events = EventCRUD(self.session)
        self.contracts = ContractCRUD(self.session)
        self.users = UserCRUD(self.session)
        self.serializer = EventSerializer()

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

    def _ensure_owner_or_admin(self, me: User, owner_id: Optional[int]) -> None:
        if not (
            Permission.is_admin(me) or (owner_id is not None and me.id == owner_id)
        ):
            raise PermissionError("Accès refusé.")

    def _validate_dates(self, start: datetime, end: datetime) -> None:
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise ValueError("date_start et date_end doivent être des datetime.")
        if end <= start:
            raise ValueError("date_end doit être postérieure à date_start.")

    # ---------- Read ----------
    def list_events(
        self,
        *,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        if Permission.is_admin(me):
            rows = self.events.get_all(filters=filters, order_by=order_by)
        else:
            rows = self.events.get_by_support_contact(me.id)
        ser = self.serializer if fields is None else EventSerializer(fields=fields)
        return ser.serialize_list(rows)

    def list_my_events(
        self, *, fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        rows = self.events.get_by_support_contact(me.id)
        ser = self.serializer if fields is None else EventSerializer(fields=fields)
        return ser.serialize_list(rows)

    def get_event(
        self,
        event_id: int,
        *,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        me = self._get_current_user()
        ev = self.events.get_by_id(event_id)
        if not ev:
            raise ValueError("Événement introuvable.")
        self._ensure_owner_or_admin(me, ev.support_contact_id)
        ser = self.serializer if fields is None else EventSerializer(fields=fields)
        return ser.serialize(ev)

    def list_by_contract(
        self,
        contract_id: int,
        *,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        # admin -> ok ; support -> restreint à ses événements
        rows = self.events.get_by_contract(contract_id)
        if not Permission.is_admin(me):
            rows = [e for e in rows if e.support_contact_id == me.id]
        ser = self.serializer if fields is None else EventSerializer(fields=fields)
        return ser.serialize_list(rows)

    def list_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        *,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        self._validate_dates(start_date, end_date)
        rows = self.events.get_by_date_range(start_date, end_date)
        if not Permission.is_admin(me):
            rows = [e for e in rows if e.support_contact_id == me.id]
        ser = self.serializer if fields is None else EventSerializer(fields=fields)
        return ser.serialize_list(rows)

    # ---------- Create ----------
    def create_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        me = self._get_current_user()
        if not Permission.create_permission(me, "event"):
            raise PermissionError("Accès refusé.")

        date_start = data.get("date_start")
        if not isinstance(date_start, datetime):
            raise ValueError("date_start must be a datetime object")
        Validations.validate_future_datetime(date_start)

        payload = {**data}
        event = self.events.create(payload)
        return self.serializer.serialize(event)

    # ---------- Update ----------
    def update_event(self, event_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        admin ou owner :
          - changer contract_id ou support_contact_id => admin-only
          - vérifie la cohérence des dates si fournies
        """
        me = self._get_current_user()
        ev = self.events.get_by_id(event_id)
        if not ev:
            raise ValueError("Événement introuvable.")

        self._ensure_owner_or_admin(me, ev.support_contact_id)

        # verrou pour champs sensibles si non-admin
        if not Permission.is_admin(me):
            forbidden = {"contract_id", "support_contact_id"}
            data = {k: v for k, v in data.items() if k not in forbidden}

        # dates optionnelles
        start = data.get("date_start", ev.date_start)
        end = data.get("date_end", ev.date_end)
        self._validate_dates(start, end)

        # si admin change contract_id → vérifier existence
        if "contract_id" in data and Permission.is_admin(me):
            cid = int(data["contract_id"])
            if not self.contracts.get_by_id(cid):
                raise ValueError("Nouveau contrat introuvable.")

        updated = self.events.update(event_id, data)
        if updated is None:
            raise ValueError("Mise à jour impossible.")
        return self.serializer.serialize(updated)

    # ---------- Assignation ----------
    def assign_support(self, event_id: int, support_user_id: int) -> Dict[str, Any]:
        """
        admin-only : réassigner l'événement à un autre technicien.
        """
        me = self._get_current_user()
        self._ensure_admin(me)

        ev = self.events.get_by_id(event_id)
        if not ev:
            raise ValueError("Événement introuvable.")

        updated = self.events.update(event_id, {"support_contact_id": support_user_id})
        if updated is None:
            raise ValueError("Assignation impossible.")
        return self.serializer.serialize(updated)

    # ---------- Delete ----------
    def delete_event(self, event_id: int) -> None:
        """
        admin ou owner (support) peuvent supprimer.
        """
        me = self._get_current_user()
        ev = self.events.get_by_id(event_id)
        if not ev:
            raise ValueError("Événement introuvable.")

        self._ensure_owner_or_admin(me, ev.support_contact_id)

        ok = self.events.delete(event_id)
        if not ok:
            raise ValueError("Suppression impossible.")
