import datetime as dt
from decimal import Decimal
import pytest
from crm.models import User, Client, Contract, Event
from sqlalchemy.exc import IntegrityError


def test_create_user_with_valid_role(db_session):
    """Création simple d'un utilisateur avec rôle valide."""
    user = User(username="Eva", password_hash="secure", role="sales")
    db_session.add(user)
    db_session.flush()
    assert user.id is not None
    assert (user.role == "sales") is True


def test_sales_workflow_creates_client_and_contract(db_session):
    """Scénario complet : commercial crée un client et un contrat signé."""
    sales_user = User(username="Thomas", password_hash="hash", role="sales")
    db_session.add(sales_user)

    client = Client(
        full_name="BetaCorp",
        email="contact@betacorp.com",
        phone="0677889900",
        company_name="BetaCorp SARL",
        sales_contact=sales_user,
    )
    db_session.add(client)

    contract = Contract(
        client=client,
        sales_contact=sales_user,
        amount_total=Decimal("7000.00"),
        amount_due=Decimal("2000.00"),
        is_signed=True,
    )
    db_session.add(contract)
    db_session.flush()

    assert client.id is not None
    assert contract.is_signed is True
    assert contract.client == client


def test_support_workflow_creates_event(db_session):
    """Création d'un événement par un support avec contrat valide."""
    sales_user = User(username="Dylan", password_hash="hash", role="sales")
    support_user = User(username="Mickael", password_hash="hash", role="support")
    db_session.add_all([sales_user, support_user])

    client = Client(
        full_name="Zeta Inc.",
        email="zeta@inc.com",
        phone="0612345678",
        company_name="Zeta Inc.",
        sales_contact=sales_user,
    )
    db_session.add(client)

    contract = Contract(
        client=client,
        sales_contact=sales_user,
        amount_total=Decimal("3000.00"),
        amount_due=Decimal("0.00"),
        is_signed=True,
    )
    db_session.add(contract)

    event = Event(
        contract=contract,
        support_contact=support_user,
        date_start=dt.datetime(2025, 12, 5, 9, 0),
        date_end=dt.datetime(2025, 12, 5, 17, 0),
        location="Lille",
        attendees=80,
    )
    db_session.add(event)
    db_session.flush()

    assert event.id is not None
    assert event.contract == contract
    assert event.support_contact == support_user


def test_create_event_with_invalid_dates_should_fail(db_session):
    """Échec si date_end est avant date_start."""
    sales_user = User(username="InvalidSupport", password_hash="x", role="support")
    db_session.add(sales_user)

    user = User(username="Patrick", password_hash="x", role="sales")

    client = Client(
        full_name="SNCF",
        email="sncf@contact.fr",
        phone="0147253636",
        company_name="SNCF",
        sales_contact=user,
    )

    contract = Contract(
        client=client,  # Sauter vérif car test date uniquement
        sales_contact=sales_user,
        amount_total=Decimal("1000.00"),
        amount_due=Decimal("500.00"),
        is_signed=True,
    )
    db_session.add(contract)
    db_session.flush()

    with pytest.raises(ValueError):
        Event(
            contract=contract,
            support_contact=sales_user,
            date_start=dt.datetime(2025, 12, 10, 18, 0),
            date_end=dt.datetime(2025, 12, 10, 10, 0),
            location="Test",
            attendees=20,
        )


def test_update_contract_due_amount(db_session):
    """Mise à jour du montant dû sur un contrat."""
    user = User(username="Patrick", password_hash="x", role="sales")
    client = Client(
        full_name="SNCF",
        email="sncf@contact.fr",
        phone="0147253636",
        company_name="SNCF",
        sales_contact=user,
    )
    contract = Contract(
        client=client,
        sales_contact=user,
        amount_total=Decimal("5000.00"),
        amount_due=Decimal("2000.00"),
        is_signed=True,
    )
    db_session.add_all([user, client, contract])
    db_session.flush()

    contract.__setattr__("amount_due", Decimal("1000.00"))
    db_session.flush()
    assert (contract.amount_due == Decimal("1000.00")) is True
