import pytest
import datetime as dt
from decimal import Decimal
from crm import models  # Charge les classes sinon ne fonctionne pas
from crm.models import User, Client, Contract, Event


@pytest.fixture
def sample_users(db_session):
    users = [
        User(username="sales1", password_hash="x", role="sales"),
        User(username="sales2", password_hash="x", role="sales"),
        User(username="supp1", password_hash="x", role="support"),
        User(username="supp2", password_hash="x", role="support"),
        User(username="manager1", password_hash="x", role="management"),
        User(username="manager2", password_hash="x", role="management"),
    ]
    db_session.add_all(users)
    db_session.flush()  # Exécute les INSERT pour générer les IDs
    return users


@pytest.fixture
def sample_clients(db_session, sample_users):
    sales1, sales2, *_ = sample_users
    clients = [
        Client(full_name="BIG Corp", email="big@corp.fr", sales_contact=sales1),
        Client(full_name="Foo Company", email="foo@company.com", sales_contact=sales2),
    ]
    db_session.add_all(clients)
    db_session.flush()
    return clients


@pytest.fixture
def sample_contracts(db_session, sample_clients, sample_users):
    sales1, sales2, *_ = sample_users
    c1, c2 = sample_clients
    contracts = [
        Contract(
            client=c1,
            sales_contact=sales1,
            amount_total=Decimal("5000.00"),
            amount_due=Decimal("1000.00"),
            is_signed=True,
        ),
        Contract(
            client=c2,
            sales_contact=sales2,
            amount_total=Decimal("8000.00"),
            amount_due=Decimal("0.00"),
            is_signed=False,
        ),
    ]
    db_session.add_all(contracts)
    db_session.flush()
    return contracts


@pytest.fixture
def sample_events(db_session, sample_contracts, sample_users):
    _, _, supp1, supp2, *_ = sample_users
    ct1, ct2 = sample_contracts
    events = [
        Event(
            contract=ct1,
            support_contact=supp1,
            date_start=dt.datetime(2025, 9, 1, 10, 0),
            date_end=dt.datetime(2025, 9, 1, 18, 0),
            location="Paris",
            attendees=100,
        ),
        Event(
            contract=ct2,
            support_contact=supp2,
            date_start=dt.datetime(2025, 10, 15, 9, 0),
            date_end=dt.datetime(2025, 10, 15, 17, 0),
            location="Lyon",
            attendees=80,
        ),
    ]
    db_session.add_all(events)
    db_session.flush()
    return events
