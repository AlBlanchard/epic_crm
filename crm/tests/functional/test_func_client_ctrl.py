import pytest
from crm.controllers.client_controller import ClientController
from crm.models.user import User
from crm.models.role import Role
from crm.models.client import Client


# --- Fixtures ---
@pytest.fixture
def client_ctrl(db_session, monkeypatch):
    ctrl = ClientController(session=db_session)

    # Créons un admin avec son rôle
    admin = User(
        employee_number=1,
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
def sales_user(db_session):
    user = User(
        employee_number=2,
        username="sales",
        email="sales@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_client(db_session, sales_user):
    client = Client(
        full_name="Jean Dubosquet",
        email="jean@example.com",
        phone="0102030405",
        company_name="Dupont SA",
        sales_contact_id=sales_user.id,
    )
    db_session.add(client)
    db_session.commit()
    return client


# --- CREATE ---
def test_create_client_success(client_ctrl, sales_user):
    ctrl, admin = client_ctrl
    data = {
        "full_name": "Alice Alice",
        "email": "alice@example.com",
        "phone": "0606060606",
        "company_name": "Alice Corp",
        "sales_contact_id": sales_user.id,
    }
    result = ctrl.create_client(data)
    assert result["full_name"] == "Alice Alice"
    assert result["email"] == "alice@example.com"


def test_create_client_non_admin_assign_other_sales(client_ctrl, db_session):
    ctrl, admin = client_ctrl
    # On force un user non-admin
    non_admin = User(
        employee_number=3,
        username="tealc",
        email="tealc@test.com",
        password_hash="hash",
    )
    db_session.add(non_admin)
    db_session.commit()
    ctrl._get_current_user = lambda: non_admin

    data = {
        "full_name": "Tealc Chapai",
        "email": "tealc@corp.com",
        "phone": "0707070707",
        "company_name": "BobCorp",
        "sales_contact_id": admin.id,  # interdit car non admin
    }
    with pytest.raises(PermissionError):
        ctrl.create_client(data)


# --- READ ---
def test_list_all_clients(client_ctrl, sample_client):
    ctrl, _ = client_ctrl
    result = ctrl.list_all()
    assert any(c["email"] == "jean@example.com" for c in result)


def test_get_client_success(client_ctrl, sample_client):
    ctrl, _ = client_ctrl
    result = ctrl.get_client(sample_client.id)
    assert result["full_name"] == "Jean Dubosquet"


def test_get_client_not_found(client_ctrl):
    ctrl, _ = client_ctrl
    with pytest.raises(ValueError):
        ctrl.get_client(9999)


# --- UPDATE ---
def test_update_client_success(client_ctrl, sample_client):
    ctrl, _ = client_ctrl
    data = {"company_name": "Nouvelle Société"}
    result = ctrl.update_client(sample_client.id, data)
    assert result["company_name"] == "Nouvelle Société"


def test_update_client_not_found(client_ctrl):
    ctrl, _ = client_ctrl
    with pytest.raises(ValueError):
        ctrl.update_client(9999, {"company_name": "Test"})


# --- DELETE ---
def test_delete_client_success(client_ctrl, sample_client):
    ctrl, _ = client_ctrl
    ctrl.delete_client(sample_client.id)
    remaining = ctrl.clients.get_by_id(sample_client.id)
    assert remaining is None


def test_delete_client_not_found(client_ctrl):
    ctrl, _ = client_ctrl
    with pytest.raises(ValueError):
        ctrl.delete_client(9999)
