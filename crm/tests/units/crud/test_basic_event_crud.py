import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError
from crm.crud.event_crud import EventCRUD


@pytest.fixture
def crud():
    return EventCRUD(session=MagicMock())


# ---------- CREATE ----------
def test_create_event_success(crud):
    fake_event = MagicMock()
    with patch("crm.crud.event_crud.Event", return_value=fake_event):
        result = crud.create({"name": "TestEvent"})
    crud.session.add.assert_called_once_with(fake_event)
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_event)
    assert result == fake_event


def test_create_event_integrity_error(crud):
    crud.session.add.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with patch("crm.crud.event_crud.Event", return_value=MagicMock()):
        with pytest.raises(IntegrityError):
            crud.create({"name": "TestEvent"})
    crud.session.rollback.assert_called_once()


def test_create_event_generic_error(crud):
    crud.session.add.side_effect = Exception("boom")
    with patch("crm.crud.event_crud.Event", return_value=MagicMock()):
        with pytest.raises(Exception):
            crud.create({"name": "TestEvent"})
    crud.session.rollback.assert_called_once()


def test_create_note_success(crud):
    fake_note = MagicMock()
    with patch("crm.crud.event_crud.EventNote", return_value=fake_note):
        result = crud.create_note({"event_id": 1, "note": "ok"})
    crud.session.add.assert_called_once_with(fake_note)
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_note)
    assert result == fake_note


# ---------- READ ----------
def test_get_all_calls_get_entities(crud):
    with patch.object(crud, "get_entities", return_value=["e1"]) as mock_get:
        result = crud.get_all()
    assert result == ["e1"]
    mock_get.assert_called_once()


def test_get_by_id(crud):
    with patch("crm.crud.event_crud.Event", autospec=True) as FakeEvent:
        crud.session.get.return_value = "event"
        result = crud.get_by_id(1)
        crud.session.get.assert_called_once_with(FakeEvent, 1)
        assert result == "event"


def test_get_by_contract(crud):
    crud.session.query.return_value.filter_by.return_value.all.return_value = ["e1"]
    result = crud.get_by_contract(10)
    assert result == ["e1"]


def test_get_by_support_contact(crud):
    crud.session.query.return_value.filter_by.return_value.all.return_value = ["e2"]
    result = crud.get_by_support_contact(42)
    assert result == ["e2"]


def test_get_notes(crud):
    crud.session.query.return_value.filter_by.return_value.all.return_value = ["n1"]
    result = crud.get_notes(5)
    assert result == ["n1"]


# ---------- UPDATE ----------
def test_update_event_success(crud):
    fake_event = MagicMock()
    crud.session.get.return_value = fake_event
    result = crud.update(1, {"name": "Updated"})
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_event)
    assert result == fake_event
    assert fake_event.name == "Updated"


def test_update_event_not_found(crud):
    crud.session.get.return_value = None
    result = crud.update(1, {"name": "X"})
    assert result is None


def test_update_event_integrity_error(crud):
    fake_event = MagicMock()
    crud.session.get.return_value = fake_event
    crud.session.commit.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with pytest.raises(IntegrityError):
        crud.update(1, {"name": "X"})
    crud.session.rollback.assert_called_once()


def test_update_event_generic_error(crud):
    fake_event = MagicMock()
    crud.session.get.return_value = fake_event
    crud.session.commit.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.update(1, {"name": "X"})
    crud.session.rollback.assert_called_once()


# ---------- DELETE ----------
def test_delete_event_success(crud):
    fake_event = MagicMock()
    crud.session.get.return_value = fake_event
    result = crud.delete(1)
    crud.session.delete.assert_called_once_with(fake_event)
    crud.session.commit.assert_called_once()
    assert result is True


def test_delete_event_not_found(crud):
    crud.session.get.return_value = None
    result = crud.delete(1)
    assert result is False


def test_delete_event_generic_error(crud):
    fake_event = MagicMock()
    crud.session.get.return_value = fake_event
    crud.session.delete.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.delete(1)
    crud.session.rollback.assert_called_once()


def test_delete_note_success(crud):
    fake_note = MagicMock()
    with patch("crm.crud.event_crud.EventNote", autospec=True) as FakeNote:
        crud.session.get.return_value = fake_note
        result = crud.delete_note(2)
    crud.session.delete.assert_called_once_with(fake_note)
    crud.session.commit.assert_called_once()
    assert result is True


def test_delete_note_not_found(crud):
    crud.session.get.return_value = None
    result = crud.delete_note(2)
    assert result is False


def test_delete_note_generic_error(crud):
    fake_note = MagicMock()
    crud.session.get.return_value = fake_note
    crud.session.delete.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.delete_note(2)
    crud.session.rollback.assert_called_once()
