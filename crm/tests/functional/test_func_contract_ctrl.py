import pytest
from decimal import Decimal
from crm.controllers.contract_controller import ContractController
from crm.models.user import User
from crm.models.role import Role
from crm.models.client import Client
from crm.models.contract import Contract


# --- Fixtures ---
@pytest.fixture
def contract_ctrl(db_session, monkeypatch):
    ctrl = ContractController(session=db_session)

    # Créons un admin avec son rôle
    admin = User(
        employee_number=10,
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
        employee_number=11,
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
        full_name="Client Test",
        email="client@example.com",
        phone="0102030405",
        company_name="TestCorp",
        sales_contact_id=sales_user.id,
    )
    db_session.add(client)
    db_session.commit()
    return client


@pytest.fixture
def sample_contract(db_session, sample_client):
    contract = Contract(
        client_id=sample_client.id,
        amount_total=Decimal("1000.00"),
        amount_due=Decimal("500.00"),
        is_signed=False,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


# --- CREATE ---
def test_create_contract_success(contract_ctrl, sample_client):
    ctrl, _ = contract_ctrl
    data = {
        "client_id": sample_client.id,
        "amount_total": Decimal("2000.00"),
        "amount_due": Decimal("1000.00"),
        "is_signed": False,
    }
    result = ctrl.create_contract(data)
    assert result["amount_total"] == Decimal("2000.00")
    assert result["is_signed"] is False


# --- READ ---
def test_get_contract_success(contract_ctrl, sample_contract):
    ctrl, _ = contract_ctrl
    result = ctrl.get_contract(sample_contract.id)
    assert result["amount_total"] == Decimal("1000.00")


def test_get_contract_not_found(contract_ctrl):
    ctrl, _ = contract_ctrl
    with pytest.raises(ValueError):
        ctrl.get_contract(9999)


def test_list_all_contracts(contract_ctrl, sample_contract):
    ctrl, _ = contract_ctrl
    results = ctrl.list_all()
    assert any(c["id"] == sample_contract.id for c in results)


# --- UPDATE ---
def test_update_contract_success(contract_ctrl, sample_contract):
    ctrl, _ = contract_ctrl
    data = {"amount_due": Decimal("250.00")}
    result = ctrl.update_contract(sample_contract.id, data)
    assert result["amount_due"] == Decimal("250.00")


def test_update_contract_not_found(contract_ctrl):
    ctrl, _ = contract_ctrl
    with pytest.raises(ValueError):
        ctrl.update_contract(9999, {"amount_due": Decimal("10.00")})


# --- DELETE ---
def test_delete_contract_success(contract_ctrl, sample_contract):
    ctrl, _ = contract_ctrl
    ctrl.delete_contract(sample_contract.id)
    remaining = ctrl.contracts.get_by_id(sample_contract.id)
    assert remaining is None


def test_delete_contract_not_found(contract_ctrl):
    ctrl, _ = contract_ctrl
    with pytest.raises(ValueError):
        ctrl.delete_contract(9999)
