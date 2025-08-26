from typing import Dict, Any, Optional, List
from datetime import datetime
from .base import AbstractController
from ..auth.permission import Permission
from ..crud.event_crud import EventCRUD
from ..crud.contract_crud import ContractCRUD
from ..crud.user_crud import UserCRUD
from ..serializers.event_serializer import EventSerializer, EventNoteSerializer
from ..utils.validations import Validations
from ..utils.app_state import AppState


class EventController(AbstractController):
    """Logique métier Événements : admin -> tout, support -> ses événements."""

    def _setup_services(self) -> None:
        self.events = EventCRUD(self.session)
        self.contracts = ContractCRUD(self.session)
        self.users = UserCRUD(self.session)
        self.serializer = EventSerializer()
        self.app_state = AppState()
        self.note_serializer = EventNoteSerializer()

    # ---------- Read ----------

    def list_all(
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

    def list_event_notes(self, event_id: int) -> List[Dict[str, Any]]:
        me = self._get_current_user()
        if not Permission.read_permission(me, "event"):
            raise PermissionError("Accès refusé.")

        notes = self.events.get_notes(event_id)
        if not notes:
            raise ValueError("Notes introuvables.")

        return self.note_serializer.serialize_list(notes)

    def get_support_contact_id(self, event_id: int) -> Optional[int]:
        me = self._get_current_user()
        if not Permission.read_permission(me, "event"):
            raise PermissionError("Accès refusé.")

        event = self.events.get_by_id(event_id)
        if not event:
            return None
        return event.support_contact_id

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

    def create_note(self, event_id: int, note: str):
        me = self._get_current_user()
        ev = self.events.get_by_id(event_id)
        if not ev:
            raise ValueError("Événement introuvable.")

        if not Permission.update_permission(me, "event"):
            raise PermissionError("Accès refusé.")

        note = self.events.create_note({"event_id": event_id, "note": note})
        if not note:
            raise ValueError("Création de la note impossible.")

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

        # verrou pour champs sensibles si non admin
        if not Permission.is_admin(me):
            forbidden = {"contract_id"}
            data = {k: v for k, v in data.items() if k not in forbidden}

        # dates optionnelles
        start = data.get("date_start", ev.date_start)
        end = data.get("date_end", ev.date_end)
        Validations.validate_date_order(start, end)

        # si admin change contract_id, vérifie son existence
        if "contract_id" in data and Permission.is_admin(me):
            cid = int(data["contract_id"])
            if not self.contracts.get_by_id(cid):
                raise ValueError("Nouveau contrat introuvable.")

        updated = self.events.update(event_id, data)
        if updated is None:
            raise ValueError("Mise à jour impossible.")
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

    def delete_note(self, event_id: int, note_id: int) -> None:
        me = self._get_current_user()
        owner_id = self.get_support_contact_id(event_id)
        if not Permission.update_permission(me, "event", owner_id=owner_id):
            raise PermissionError("Accès refusé.")

        try:
            self.events.delete_note(note_id)
        except ValueError:
            raise ValueError("Note introuvable.")
