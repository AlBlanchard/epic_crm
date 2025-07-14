import pytest
from crm.models import Event, Contract
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta


def test_create_valid_event(db_session, sample_contracts, sample_users):
    """Création d'un Event valide."""
    contract = sample_contracts[0]
    support = sample_users[2]

    event = Event(
        contract=contract,
        support_contact=support,
        date_start=datetime(2025, 10, 1, 10, 0),
        date_end=datetime(2025, 10, 1, 18, 0),
        location="Paris",
        attendees=150,
        notes="Réunion annuelle",
    )
    db_session.add(event)
    db_session.flush()

    assert event.id is not None
    assert (event.date_end > event.date_start) is True
    assert (event.attendees == 150) is True


def test_event_invalid_attendees_type():
    """Erreur si attendees n'est pas un int."""
    with pytest.raises(ValueError, match="must be an integer"):
        Event(
            contract_id=1,
            date_start=datetime(2025, 10, 1, 10),
            date_end=datetime(2025, 10, 1, 18),
            attendees="cinquante",
        )


def test_event_negative_attendees():
    """Erreur si attendees < 0."""
    with pytest.raises(ValueError, match="cannot be negative"):
        Event(
            contract_id=1,
            date_start=datetime(2025, 10, 1, 10),
            date_end=datetime(2025, 10, 1, 18),
            attendees=-5,
        )


def test_event_zero_attendees():
    """Erreur si attendees == 0."""
    with pytest.raises(ValueError, match="cannot be negative"):
        Event(
            contract_id=1,
            date_start=datetime(2025, 10, 1, 10),
            date_end=datetime(2025, 10, 1, 18),
            attendees=0,
        )


def test_event_invalid_date_type():
    """Erreur si date_start/date_end ne sont pas des datetime."""
    with pytest.raises(ValueError, match="must be a datetime object"):
        Event(
            contract_id=1,
            date_start="2025-01-01",
            date_end=datetime(2025, 1, 1, 18),
            attendees=10,
        )


def test_event_end_before_start():
    """Erreur si date_end < date_start."""
    with pytest.raises(ValueError, match="date_end must be after date_start"):
        Event(
            contract_id=1,
            date_start=datetime(2025, 10, 1, 18),
            date_end=datetime(2025, 10, 1, 10),
            attendees=10,
        )


def test_event_missing_contract(db_session):
    """Erreur si contract_id absent (clé étrangère requise)."""
    event = Event(
        date_start=datetime(2025, 10, 1, 10),
        date_end=datetime(2025, 10, 1, 18),
        attendees=20,
        location="Nice",
    )
    db_session.add(event)
    with pytest.raises(IntegrityError):
        db_session.flush()
