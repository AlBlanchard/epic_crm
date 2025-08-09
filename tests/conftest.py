import pytest
import datetime as dt
import sqlite3
from decimal import Decimal
from crm.models import models  # Charge les classes sinon ne fonctionne pas
from crm.models.models import User, Client, Contract, Event
from sqlalchemy.orm import sessionmaker
from crm.database import Base


# Configuration de la base de données pour les tests
# "function" à la place de "session" pour réinitialiser la base de données entre chaque test
@pytest.fixture(scope="function", autouse=True)
def setup_database(engine_fixture):
    Base.metadata.create_all(bind=engine_fixture)
    yield
    Base.metadata.drop_all(bind=engine_fixture)


TEST_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(TEST_URL, echo=False, future=True)


# Active les clés étrangères
@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, _):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.execute("PRAGMA foreign_keys = ON")


@pytest.fixture(scope="session")
def engine_fixture():
    return engine


@pytest.fixture(scope="function")
def db_session(engine_fixture):
    Session = sessionmaker(bind=engine_fixture, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def sample_users(db_session, sales_dept, support_dept, management_dept):
    users = [
        User(
            employee_number=1,
            username="sales1",
            email="sales1@test.com",
            password_hash="hash",
            department=sales_dept,
        ),
        User(
            employee_number=2,
            username="sales2",
            email="sales2@test.com",
            password_hash="hash",
            department=sales_dept,
        ),
        User(
            employee_number=3,
            username="supp1",
            email="supp1@test.com",
            password_hash="hash",
            department=support_dept,
        ),
        User(
            employee_number=4,
            username="supp2",
            email="supp2@test.com",
            password_hash="hash",
            department=support_dept,
        ),
        User(
            employee_number=5,
            username="manager1",
            email="manager1@test.com",
            password_hash="hash",
            department=management_dept,
        ),
        User(
            employee_number=6,
            username="manager2",
            email="manager2@test.com",
            password_hash="hash",
            department=management_dept,
        ),
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


@pytest.fixture
def departments(db_session):
    """Fixture pour créer tous les départements"""
    departments = [
        Department(name="sales"),
        Department(name="support"),
        Department(name="management"),
    ]
    db_session.add_all(departments)
    db_session.flush()
    return departments


@pytest.fixture
def sales_dept(db_session, departments):
    """Fixture pour récupérer le département des ventes"""
    return next(dept for dept in departments if dept.name == "sales")


@pytest.fixture
def support_dept(db_session, departments):
    """Fixture pour récupérer le département de support"""
    return next(dept for dept in departments if dept.name == "support")


@pytest.fixture
def management_dept(db_session, departments):
    """Fixture pour récupérer le département de management"""
    return next(dept for dept in departments if dept.name == "management")
