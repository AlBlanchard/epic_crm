import pytest
import datetime
from crm.models.event import Event, EventNote
from crm.models.user import User


@pytest.fixture
def fake_user():
    u = User()
    u.id = 1
    u.username = "alice"
    return u


def test_repr_basic():
    e = Event()
    e.id = 1
    e.location = "Paris"
    e.attendees = 100
    assert repr(e) == "<Event(id=1, location='Paris', attendees=100)>"


def test_support_contact_name_with_user(fake_user):
    e = Event()
    e.support_contact = fake_user
    assert e.support_contact_name == "alice"


def test_support_contact_name_none():
    e = Event()
    e.support_contact = None
    assert e.support_contact_name == "Aucun contact"


def test_is_assigned_true(fake_user):
    e = Event()
    e.support_contact = fake_user
    assert e.is_assigned is True


def test_is_assigned_false():
    e = Event()
    e.support_contact = None
    assert e.is_assigned is False


# -------- VALIDATE DATES --------


def test_validate_dates_valid_start_end():
    e = Event()
    start = datetime.datetime(2025, 1, 1, 10, 0)
    end = datetime.datetime(2025, 1, 1, 12, 0)
    assert e.validate_dates("date_start", start) == start
    e.date_start = start
    assert e.validate_dates("date_end", end) == end


def test_validate_dates_invalid_type():
    e = Event()
    with pytest.raises(ValueError):
        e.validate_dates("date_start", "not-a-datetime")


def test_validate_dates_end_before_start():
    e = Event()
    e.date_start = datetime.datetime(2025, 1, 1, 12, 0)
    with pytest.raises(ValueError):
        e.validate_dates("date_end", datetime.datetime(2025, 1, 1, 10, 0))


def test_validate_dates_start_after_end():
    e = Event()
    e.date_end = datetime.datetime(2025, 1, 1, 9, 0)
    with pytest.raises(ValueError):
        e.validate_dates("date_start", datetime.datetime(2025, 1, 1, 12, 0))


# -------- VALIDATE ATTENDEES --------


def test_validate_attendees_valid():
    e = Event()
    assert e.validate_attendees("attendees", 10) == 10


def test_validate_attendees_invalid_type():
    e = Event()
    with pytest.raises(ValueError):
        e.validate_attendees("attendees", "ten")


def test_validate_attendees_negative_or_zero():
    e = Event()
    with pytest.raises(ValueError):
        e.validate_attendees("attendees", 0)
    with pytest.raises(ValueError):
        e.validate_attendees("attendees", -5)


# -------- EVENT NOTE --------


def test_eventnote_repr():
    note = EventNote()
    note.id = 5
    note.event_id = 42
    assert repr(note) == "<EventNote(id=5, event_id=42)>"
