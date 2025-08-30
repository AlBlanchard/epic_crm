import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from crm.controllers.event_controller import EventController


@pytest.fixture
def controller():
    ctrl = EventController(session=MagicMock())
    ctrl._setup_services()
    ctrl.events = MagicMock()
    ctrl.contracts = MagicMock()
    ctrl.users = MagicMock()
    ctrl.serializer = MagicMock()
    ctrl.note_serializer = MagicMock()
    ctrl.contract_ctrl = MagicMock()
    ctrl._get_current_user = MagicMock(return_value=MagicMock(id=1))
    return ctrl


# ---------- list_all ----------
def test_list_all_success(controller):
    controller.events.get_all.return_value = [MagicMock()]
    controller.serializer.serialize_list.return_value = [{"id": 1}]
    with patch(
        "crm.controllers.event_controller.Permission.read_permission", return_value=True
    ):
        result = controller.list_all()
    assert result == [{"id": 1}]


def test_list_all_no_permission(controller):
    with patch(
        "crm.controllers.event_controller.Permission.read_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.list_all()


# ---------- get_event ----------
def test_get_event_success(controller):
    fake_event = MagicMock(id=2)
    controller.events.get_by_id.return_value = fake_event
    controller.serializer.serialize.return_value = {"id": 2}
    with patch(
        "crm.controllers.event_controller.Permission.read_permission", return_value=True
    ):
        result = controller.get_event(2)
    assert result == {"id": 2}


def test_get_event_not_found(controller):
    controller.events.get_by_id.return_value = None
    with patch(
        "crm.controllers.event_controller.Permission.read_permission", return_value=True
    ):
        with pytest.raises(ValueError):
            controller.get_event(999)


# ---------- list_event_notes ----------
def test_list_event_notes_success(controller):
    controller.events.get_notes.return_value = [MagicMock()]
    controller.note_serializer.serialize_list.return_value = [{"note": "ok"}]
    with patch(
        "crm.controllers.event_controller.Permission.read_permission", return_value=True
    ):
        result = controller.list_event_notes(1)
    assert result == [{"note": "ok"}]


def test_list_event_notes_not_found(controller):
    controller.events.get_notes.return_value = None
    with patch(
        "crm.controllers.event_controller.Permission.read_permission", return_value=True
    ):
        with pytest.raises(ValueError):
            controller.list_event_notes(1)


# ---------- get_support_contact_id ----------
def test_get_support_contact_id_success(controller):
    fake_event = MagicMock(support_contact_id=42)
    controller.events.get_by_id.return_value = fake_event
    with patch(
        "crm.controllers.event_controller.Permission.read_permission", return_value=True
    ):
        assert controller.get_support_contact_id(1) == 42


def test_get_support_contact_id_none(controller):
    controller.events.get_by_id.return_value = None
    with patch(
        "crm.controllers.event_controller.Permission.read_permission", return_value=True
    ):
        assert controller.get_support_contact_id(1) is None


# ---------- create_event ----------
def test_create_event_success(controller):
    data = {"date_start": datetime.now() + timedelta(days=1), "contract_id": 5}
    fake_event = MagicMock(id=1)
    controller.events.create.return_value = fake_event
    controller.serializer.serialize.return_value = {"id": 1}
    controller.contract_ctrl.is_contract_signed.return_value = True
    with patch(
        "crm.controllers.event_controller.Permission.create_permission",
        return_value=True,
    ), patch("crm.controllers.event_controller.Validations.validate_future_datetime"):
        result = controller.create_event(data)
    assert result == {"id": 1}


def test_create_event_no_permission(controller):
    data = {"date_start": datetime.now() + timedelta(days=1)}
    with patch(
        "crm.controllers.event_controller.Permission.create_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.create_event(data)


def test_create_event_invalid_date(controller):
    data = {"date_start": "not_a_date"}
    with patch(
        "crm.controllers.event_controller.Permission.create_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.create_event(data)


def test_create_event_unsigned_contract(controller):
    data = {"date_start": datetime.now() + timedelta(days=1), "contract_id": 5}
    controller.contract_ctrl.is_contract_signed.return_value = False
    with patch(
        "crm.controllers.event_controller.Permission.create_permission",
        return_value=True,
    ), patch("crm.controllers.event_controller.Validations.validate_future_datetime"):
        with pytest.raises(ValueError):
            controller.create_event(data)


# ---------- create_note ----------
def test_create_note_success(controller):
    controller.events.get_by_id.return_value = MagicMock()
    controller.events.create_note.return_value = MagicMock()
    with patch(
        "crm.controllers.event_controller.Permission.update_permission",
        return_value=True,
    ), patch.object(controller, "get_support_contact_id", return_value=1):
        controller.create_note(1, "note")
        controller.events.create_note.assert_called_once()


def test_create_note_event_not_found(controller):
    controller.events.get_by_id.return_value = None
    with patch(
        "crm.controllers.event_controller.Permission.update_permission",
        return_value=True,
    ), patch.object(controller, "get_support_contact_id", return_value=1):
        with pytest.raises(ValueError):
            controller.create_note(1, "note")


def test_create_note_creation_failed(controller):
    controller.events.get_by_id.return_value = MagicMock()
    controller.events.create_note.return_value = None
    with patch(
        "crm.controllers.event_controller.Permission.update_permission",
        return_value=True,
    ), patch.object(controller, "get_support_contact_id", return_value=1):
        with pytest.raises(ValueError):
            controller.create_note(1, "note")


# ---------- update_event ----------
def test_update_event_success_admin(controller):
    fake_event = MagicMock(
        id=2, support_contact_id=1, date_start=datetime.now(), date_end=datetime.now()
    )
    controller.events.get_by_id.return_value = fake_event
    controller.events.update.return_value = fake_event
    controller.serializer.serialize.return_value = {"id": 2}
    controller.contracts.get_by_id.return_value = MagicMock()
    with patch(
        "crm.controllers.event_controller.Permission.update_permission",
        return_value=True,
    ), patch(
        "crm.controllers.event_controller.Permission.is_admin", return_value=True
    ), patch(
        "crm.controllers.event_controller.Validations.validate_date_order"
    ):
        result = controller.update_event(2, {"contract_id": 5})
    assert result == {"id": 2}


def test_update_event_non_admin_filters_fields(controller):
    fake_event = MagicMock(
        id=2, support_contact_id=1, date_start=datetime.now(), date_end=datetime.now()
    )
    controller.events.get_by_id.return_value = fake_event
    controller.events.update.return_value = fake_event
    controller.serializer.serialize.return_value = {"id": 2}
    with patch(
        "crm.controllers.event_controller.Permission.update_permission",
        return_value=True,
    ), patch(
        "crm.controllers.event_controller.Permission.is_admin", return_value=False
    ), patch(
        "crm.controllers.event_controller.Validations.validate_date_order"
    ):
        controller.update_event(2, {"contract_id": 5, "foo": "bar"})
        args, kwargs = controller.events.update.call_args
        assert "contract_id" not in kwargs["data"] if "data" in kwargs else args[1]


def test_update_event_not_found(controller):
    controller.events.get_by_id.return_value = None
    with pytest.raises(ValueError):
        controller.update_event(2, {})


# ---------- delete_event ----------
def test_delete_event_success(controller):
    controller.events.get_by_id.return_value = MagicMock()
    controller.events.delete.return_value = True
    with patch(
        "crm.controllers.event_controller.Permission.delete_permission",
        return_value=True,
    ):
        controller.delete_event(1)
        controller.events.delete.assert_called_once_with(1)


def test_delete_event_not_found(controller):
    controller.events.get_by_id.return_value = None
    with patch(
        "crm.controllers.event_controller.Permission.delete_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.delete_event(1)


def test_delete_event_failed(controller):
    controller.events.get_by_id.return_value = MagicMock()
    controller.events.delete.return_value = False
    with patch(
        "crm.controllers.event_controller.Permission.delete_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.delete_event(1)


# ---------- delete_note ----------
def test_delete_note_success(controller):
    controller.events.delete_note.return_value = True
    with patch(
        "crm.controllers.event_controller.Permission.update_permission",
        return_value=True,
    ), patch.object(controller, "get_support_contact_id", return_value=1):
        controller.delete_note(1, 1)
        controller.events.delete_note.assert_called_once_with(1)


def test_delete_note_not_found(controller):
    controller.events.delete_note.side_effect = ValueError
    with patch(
        "crm.controllers.event_controller.Permission.update_permission",
        return_value=True,
    ), patch.object(controller, "get_support_contact_id", return_value=1):
        with pytest.raises(ValueError):
            controller.delete_note(1, 1)
