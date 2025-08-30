import pytest
import datetime
from decimal import Decimal

from crm.controllers.event_controller import EventController
from crm.models.user import User, Role
from crm.models.client import Client
from crm.models.contract import Contract
from crm.models.event import Event, EventNote


# --- Fixtures ---
@pytest.fixture
def event_ctrl(db_session, monkeypatch):
    ctrl = EventController(session=db_session)

    # admin user
    admin = User(
        employee_number=20,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
    )
    role_admin = Role(name="admin")
    db_session.add_all([admin, role_admin])
    db_session.commit()
    admin.add_role(role_admin, db_session)
    db_session.commit()

    monkeypatch.setattr(ctrl, "_get_current_user", lambda: admin)
    return ctrl, admin


@pytest.fixture
def sample_client(db_session):
    user = User(
        employee_number=21,
        username="sales",
        email="sales@test.com",
        password_hash="hash",
    )
    client = Client(
        full_name="Client Event",
        email="client.event@example.com",
        phone="0600000000",
        company_name="EventCorp",
        sales_contact=user,
    )
    db_session.add_all([user, client])
    db_session.commit()
    return client


@pytest.fixture
def signed_contract(db_session, sample_client):
    contract = Contract(
        client_id=sample_client.id,
        amount_total=Decimal("1000.00"),
        amount_due=Decimal("500.00"),
        is_signed=True,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def unsigned_contract(db_session, sample_client):
    contract = Contract(
        client_id=sample_client.id,
        amount_total=Decimal("500.00"),
        amount_due=Decimal("200.00"),
        is_signed=False,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def sample_event(db_session, signed_contract):
    ev = Event(
        contract_id=signed_contract.id,
        date_start=datetime.datetime.now() + datetime.timedelta(days=1),
        date_end=datetime.datetime.now() + datetime.timedelta(days=2),
        location="Paris",
        attendees=50,
    )
    db_session.add(ev)
    db_session.commit()
    return ev


# --- CREATE ---
def test_create_event_success(event_ctrl, signed_contract):
    ctrl, _ = event_ctrl
    data = {
        "contract_id": signed_contract.id,
        "date_start": datetime.datetime.now() + datetime.timedelta(days=1),
        "date_end": datetime.datetime.now() + datetime.timedelta(days=2),
        "location": "Lyon",
        "attendees": 20,
    }
    result = ctrl.create_event(data)
    assert result["location"] == "Lyon"


def test_create_event_contract_not_signed(event_ctrl, unsigned_contract):
    ctrl, _ = event_ctrl
    data = {
        "contract_id": unsigned_contract.id,
        "date_start": datetime.datetime.now() + datetime.timedelta(days=1),
        "date_end": datetime.datetime.now() + datetime.timedelta(days=2),
        "location": "Nice",
        "attendees": 15,
    }
    with pytest.raises(ValueError, match="Contrat non signé"):
        ctrl.create_event(data)


def test_create_event_date_past(event_ctrl, signed_contract):
    ctrl, _ = event_ctrl
    data = {
        "contract_id": signed_contract.id,
        "date_start": datetime.datetime.now() - datetime.timedelta(days=1),
        "date_end": datetime.datetime.now(),
        "location": "Marseille",
        "attendees": 10,
    }
    with pytest.raises(ValueError, match="futur"):
        ctrl.create_event(data)


# --- READ ---
def test_get_event_success(event_ctrl, sample_event):
    ctrl, _ = event_ctrl
    result = ctrl.get_event(sample_event.id)
    assert result["location"] == "Paris"


def test_get_event_not_found(event_ctrl):
    ctrl, _ = event_ctrl
    with pytest.raises(ValueError):
        ctrl.get_event(9999)


def test_list_all_events(event_ctrl, sample_event):
    ctrl, _ = event_ctrl
    results = ctrl.list_all()
    assert any(e["id"] == sample_event.id for e in results)


# --- NOTES ---
def test_add_and_list_notes(event_ctrl, sample_event):
    ctrl, _ = event_ctrl
    ctrl.create_note(sample_event.id, "Préparation logistique")
    notes = ctrl.list_event_notes(sample_event.id)
    assert any("Préparation logistique" in n["note"] for n in notes)


def test_delete_note_success(event_ctrl, sample_event, db_session):
    ctrl, _ = event_ctrl
    note = EventNote(event_id=sample_event.id, note="A supprimer")
    db_session.add(note)
    db_session.commit()

    ctrl.delete_note(sample_event.id, note.id)
    remaining = db_session.get(EventNote, note.id)
    assert remaining is None


def test_delete_note_not_found(event_ctrl, sample_event):
    ctrl, _ = event_ctrl
    with pytest.raises(ValueError, match="introuvable"):
        ctrl.delete_note(sample_event.id, 9999)


# --- UPDATE ---
def test_update_event_success(event_ctrl, sample_event):
    ctrl, _ = event_ctrl
    data = {"location": "Bordeaux"}
    result = ctrl.update_event(sample_event.id, data)
    assert result["location"] == "Bordeaux"


def test_update_event_not_found(event_ctrl):
    ctrl, _ = event_ctrl
    with pytest.raises(ValueError):
        ctrl.update_event(9999, {"location": "Lille"})


def test_update_event_invalid_dates(event_ctrl, sample_event):
    ctrl, _ = event_ctrl
    data = {
        "date_start": datetime.datetime.now() + datetime.timedelta(days=5),
        "date_end": datetime.datetime.now() + datetime.timedelta(days=1),
    }
    with pytest.raises(ValueError, match="postérieure"):
        ctrl.update_event(sample_event.id, data)


# --- DELETE ---
def test_delete_event_success(event_ctrl, sample_event):
    ctrl, _ = event_ctrl
    ctrl.delete_event(sample_event.id)
    assert ctrl.events.get_by_id(sample_event.id) is None


def test_delete_event_not_found(event_ctrl):
    ctrl, _ = event_ctrl
    with pytest.raises(ValueError):
        ctrl.delete_event(9999)
