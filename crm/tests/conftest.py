import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from unittest.mock import MagicMock

from crm.models.base import AbstractBase
from crm.controllers.base import AbstractController
from crm.controllers.client_controller import ClientController
from crm.controllers.contract_controller import ContractController
from crm.controllers.event_controller import EventController
from crm.controllers.user_controller import UserController
from crm.models.user import User
from crm.models.role import Role
from crm.models.user_role import UserRole


# --- Fixtures utilisateurs / sessions ---
@pytest.fixture
def fake_user():
    """Retourne un faux utilisateur standard."""
    user = MagicMock()
    user.id = 1
    user.username = "testuser"
    user.email = "user@test.com"
    user.roles = []
    return user


@pytest.fixture
def fake_admin():
    """Retourne un faux administrateur."""
    admin = MagicMock()
    admin.id = 99
    admin.username = "admin"
    admin.email = "admin@test.com"
    admin.roles = [MagicMock(name="admin")]
    return admin


@pytest.fixture
def fake_session():
    """Session SQLAlchemy mockée pour tous les contrôleurs."""
    return MagicMock()


# --- Fixtures entities ---
@pytest.fixture
def fake_client(fake_user):
    """Retourne un faux client lié à un commercial."""
    client = MagicMock()
    client.id = 10
    client.company_name = "TestCorp"
    client.sales_contact_id = fake_user.id
    client.sales_contact = fake_user
    return client


@pytest.fixture
def fake_contract(fake_client, fake_user):
    """Retourne un faux contrat lié à un client et un commercial."""
    contract = MagicMock()
    contract.id = 20
    contract.client = fake_client
    contract.amount_total = "1000"
    contract.amount_due = "500"
    contract.is_signed = False
    contract.sales_contact_id = fake_user.id
    return contract


@pytest.fixture
def fake_event(fake_contract, fake_user):
    """Retourne un faux événement lié à un contrat et un support."""
    event = MagicMock()
    event.id = 30
    event.contract = fake_contract
    event.date_start = None
    event.date_end = None
    event.support_contact_id = fake_user.id
    return event


# --- Fixtures controllers génériques ---
@pytest.fixture
def dummy_controller_cls():
    """Retourne une classe concrète basée sur AbstractController pour tests génériques."""
    from crm.controllers.base import AbstractController

    class DummyController(AbstractController):
        def _setup_services(self):
            self.extra = "ok"

    return DummyController


@pytest.fixture
def dummy_controller(fake_session, dummy_controller_cls):
    """Instance de DummyController avec session mockée."""
    return dummy_controller_cls(session=fake_session)


# --- Fixtures utilitaires pour les permissions ---
@pytest.fixture
def allow_all_permissions(monkeypatch):
    """Patch Permission.* pour toujours retourner True."""
    from crm.auth import permission

    monkeypatch.setattr(
        permission.Permission, "has_permission", staticmethod(lambda *a, **k: True)
    )
    monkeypatch.setattr(
        permission.Permission, "read_permission", staticmethod(lambda *a, **k: True)
    )
    monkeypatch.setattr(
        permission.Permission, "create_permission", staticmethod(lambda *a, **k: True)
    )
    monkeypatch.setattr(
        permission.Permission, "update_permission", staticmethod(lambda *a, **k: True)
    )
    monkeypatch.setattr(
        permission.Permission, "delete_permission", staticmethod(lambda *a, **k: True)
    )
    monkeypatch.setattr(
        permission.Permission, "is_admin", staticmethod(lambda *a, **k: True)
    )
    yield


@pytest.fixture
def deny_all_permissions(monkeypatch):
    """Patch Permission.* pour toujours retourner False."""
    from crm.auth import permission

    monkeypatch.setattr(
        permission.Permission, "has_permission", staticmethod(lambda *a, **k: False)
    )
    monkeypatch.setattr(
        permission.Permission, "read_permission", staticmethod(lambda *a, **k: False)
    )
    monkeypatch.setattr(
        permission.Permission, "create_permission", staticmethod(lambda *a, **k: False)
    )
    monkeypatch.setattr(
        permission.Permission, "update_permission", staticmethod(lambda *a, **k: False)
    )
    monkeypatch.setattr(
        permission.Permission, "delete_permission", staticmethod(lambda *a, **k: False)
    )
    monkeypatch.setattr(
        permission.Permission, "is_admin", staticmethod(lambda *a, **k: False)
    )
    yield


# Base isolée pour les tests fonctionnels
TestingBase = declarative_base()


@pytest.fixture(scope="session")
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    return engine


@pytest.fixture(scope="session")
def tables(engine):
    # Crée toutes les tables définies par AbstractBase
    AbstractBase.metadata.create_all(engine)
    yield
    AbstractBase.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine):
    # Reset complet à chaque test
    from crm.models.base import AbstractBase

    AbstractBase.metadata.drop_all(engine)
    AbstractBase.metadata.create_all(engine)

    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, expire_on_commit=False, future=True)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def bypass_auth(monkeypatch, db_session, request):
    """
    Bypass JWT auth dans les tests fonctionnels/intégration.
    - Par défaut : admin
    - @pytest.mark.as_role("commercial") → force le sales
    - @pytest.mark.no_bypass_auth → désactive le bypass
    """

    if "no_bypass_auth" in request.keywords:
        yield
        return

    marker = request.node.get_closest_marker("as_role")
    role_name = marker.args[0] if marker else "admin"

    def fake_get_current_user(self):
        from crm.models.user import User, Role

        return (
            db_session.query(User)
            .join(User.user_roles)
            .join(Role)
            .filter(Role.name == role_name)
            .first()
        )

    monkeypatch.setattr(AbstractController, "_get_current_user", fake_get_current_user)
    yield


@pytest.fixture(scope="session")
def setup_roles_and_users(engine, tables):
    """Insère des rôles et des utilisateurs cohérents pour les tests fonctionnels/intégration."""
    from sqlalchemy.orm import Session

    session = Session(engine)

    # --- Créer les rôles ---
    role_admin = Role(name="admin")
    role_sales = Role(name="commercial")
    role_support = Role(name="support")
    session.add_all([role_admin, role_sales, role_support])
    session.commit()

    # --- Créer les users ---
    admin = User(
        employee_number=1, username="admin", email="admin@test.com", password_hash="x"
    )
    sales = User(
        employee_number=2, username="sales", email="sales@test.com", password_hash="x"
    )
    support = User(
        employee_number=3,
        username="support",
        email="support@test.com",
        password_hash="x",
    )
    session.add_all([admin, sales, support])
    session.commit()

    # --- Associer rôles ---
    session.add_all(
        [
            UserRole(user_id=admin.id, role_id=role_admin.id),
            UserRole(user_id=sales.id, role_id=role_sales.id),
            UserRole(user_id=support.id, role_id=role_support.id),
        ]
    )
    session.commit()

    yield
    session.close()


@pytest.fixture
def admin_user(db_session):
    """Crée un utilisateur admin réel en base de test."""
    # Vérifie si le rôle existe déjà
    role_admin = db_session.query(Role).filter_by(name="admin").first()
    if not role_admin:
        role_admin = Role(name="admin")
        db_session.add(role_admin)
        db_session.commit()

    user = User(
        employee_number=999,
        username="admin_test",
        email="admin@test.com",
        password_hash="fakehash",
    )
    db_session.add(user)
    db_session.commit()

    # Lie le rôle admin
    user_role = UserRole(user_id=user.id, role_id=role_admin.id)
    db_session.add(user_role)
    db_session.commit()

    return user


@pytest.fixture
def seed_roles(db_session):
    """Crée les rôles de base en base de test (function-scoped, pour chaque test)."""
    from crm.models.role import Role

    roles = ["admin", "commercial", "support", "management"]
    for r in roles:
        if not db_session.query(Role).filter_by(name=r).first():
            db_session.add(Role(name=r))
    db_session.commit()


@pytest.fixture
def seeded_users(db_session, seed_roles):  # seed_roles garantit que les rôles existent
    from crm.models.user import User, Role, UserRole

    admin = User(username="admin", email="admin@test.com", employee_number=1)
    admin.set_password("pass")
    sales = User(username="sales", email="sales@test.com", employee_number=2)
    sales.set_password("pass")

    role_admin = db_session.query(Role).filter_by(name="admin").first()
    role_sales = db_session.query(Role).filter_by(name="commercial").first()

    db_session.add_all([admin, sales])
    db_session.flush()

    db_session.add_all(
        [
            UserRole(user_id=admin.id, role_id=role_admin.id),
            UserRole(user_id=sales.id, role_id=role_sales.id),
        ]
    )
    db_session.commit()

    return {"admin": admin, "sales": sales}


@pytest.fixture
def client_ctrl(db_session):
    return ClientController(db_session)


@pytest.fixture
def contract_ctrl(db_session):
    return ContractController(db_session)


@pytest.fixture
def event_ctrl(db_session):
    return EventController(db_session)


@pytest.fixture
def user_ctrl(db_session):
    return UserController(db_session)


@pytest.fixture
def sales_user(seeded_users):
    return seeded_users["sales"]


@pytest.fixture
def other_sales_client(db_session, seeded_users):
    """Un client assigné à un commercial différent du sales_user."""
    from crm.models.client import Client

    # On prend un commercial différent de sales_user
    other_sales = seeded_users["admin"]

    client = Client(
        full_name="Other Client",
        email="other@test.com",
        phone="0101010101",
        company_name="OtherCorp",
        sales_contact_id=other_sales.id,
    )
    db_session.add(client)
    db_session.commit()
    return client
