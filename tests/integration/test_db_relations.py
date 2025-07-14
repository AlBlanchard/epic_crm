import datetime as dt
from decimal import Decimal
import pytest
from crm.models import User, Client, Contract, Event
from sqlalchemy.exc import IntegrityError


def test_full_creation_flow(db_session):
    # Création du commercial
    sales_user = User(username="Lucile", password_hash="hash", role="sales")
    db_session.add(sales_user)

    # Création du client
    client = Client(
        full_name="Macif SAM",
        email="contact@macif.fr",
        phone="0123456789",
        company_name="Macif",
        sales_contact=sales_user,
    )
    db_session.add(client)

    # Création d'un contrat signé lié au client
    contract = Contract(
        client=client,
        sales_contact=sales_user,
        amount_total=Decimal("10000.00"),
        amount_due=Decimal("5000.00"),
        is_signed=True,
    )
    db_session.add(contract)

    # Création du support
    support_user = User(username="Alexis", password_hash="hash", role="support")
    db_session.add(support_user)

    # Création de l'événement lié au contrat et au support
    event = Event(
        contract=contract,
        support_contact=support_user,
        date_start=dt.datetime(2025, 9, 1, 10, 0),
        date_end=dt.datetime(2025, 9, 1, 18, 0),
        location="Paris",
        attendees=100,
        notes="Test Event",
    )
    db_session.add(event)

    # Flush pour déclencher les contraintes et générer les IDs
    db_session.flush()

    # Vérifications relationnelles
    assert sales_user.id is not None
    assert client.sales_contact == sales_user
    assert contract.client == client
    assert contract.sales_contact == sales_user
    assert event.contract == contract
    assert event.support_contact == support_user
    assert (event.attendees == 100) is True
    assert (event.location == "Paris") is True


def test_contract_creation_without_client_should_fail(db_session):
    sales_user = User(username="Lohan", password_hash="hash", role="sales")
    db_session.add(sales_user)
    db_session.flush()

    contract = Contract(
        client=None,
        sales_contact=sales_user,
        amount_total=Decimal("1000.00"),
        amount_due=Decimal("500.00"),
        is_signed=False,
    )
    db_session.add(contract)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_event_creation_without_contract_should_fail(db_session):
    support_user = User(username="Rémi", password_hash="hash", role="support")
    db_session.add(support_user)
    db_session.flush()

    event = Event(
        contract=None,
        support_contact=support_user,
        date_start=dt.datetime(2025, 8, 1, 9, 0),
        date_end=dt.datetime(2025, 8, 1, 17, 0),
        location="Nantes",
        attendees=50,
        notes="Test sans contrat",
    )

    db_session.add(event)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_client_creation_without_sales_contact_should_fail(db_session):
    client = Client(
        full_name="Vault Tech",
        email="vault@tech.com",
        phone="0102030405",
        company_name="Vault Tech Inc.",
        sales_contact=None,
    )
    db_session.add(client)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_contract_with_due_exceeding_total_should_fail(
    db_session, sample_clients, sample_users
):
    client = sample_clients[0]
    sales = [u for u in sample_users if u.role == "sales"][0]

    with pytest.raises(ValueError, match="amount_due cannot exceed amount_total"):
        contract = Contract(
            client=client,
            sales_contact=sales,
            amount_total=Decimal("1000.00"),
            amount_due=Decimal("2000.00"),
            is_signed=True,
        )
        db_session.add(contract)
        db_session.flush()


def test_event_with_end_before_start_should_fail(
    db_session, sample_contracts, sample_users
):
    contract = sample_contracts[0]
    support = [u for u in sample_users if u.role == "support"][0]

    with pytest.raises(ValueError, match="date_end must be after date_start"):
        event = Event(
            contract=contract,
            support_contact=support,
            date_start=dt.datetime(2025, 9, 2, 18, 0),
            date_end=dt.datetime(2025, 9, 2, 10, 0),
            location="Lyon",
            attendees=30,
            notes="Invalid event timing",
        )

        db_session.add(event)
        db_session.flush()


def test_update_client_sales_contact(db_session, sample_clients, sample_users):
    client = sample_clients[0]
    new_sales = [
        u for u in sample_users if u.role == "sales" and u != client.sales_contact
    ][0]

    client.sales_contact = new_sales
    db_session.flush()

    assert client.sales_contact_id == new_sales.id
