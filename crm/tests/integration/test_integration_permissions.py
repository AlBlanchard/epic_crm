import pytest
import datetime
from decimal import Decimal

from crm.controllers.user_controller import UserController
from crm.controllers.client_controller import ClientController
from crm.controllers.contract_controller import ContractController
from crm.controllers.event_controller import EventController
from crm.models.role import Role
from crm.models.user import User
from crm.auth.permission import Permission


@pytest.fixture
def setup_roles(db_session):
    role_admin = Role(name="admin")
    role_sales = Role(name="commercial")
    role_support = Role(name="support")
    db_session.add_all([role_admin, role_sales, role_support])
    db_session.commit()
    return role_admin, role_sales, role_support


@pytest.fixture
def users_with_roles(db_session, setup_roles):
    role_admin, role_sales, role_support = setup_roles

    admin = User(
        employee_number=1, username="admin", email="a@a.com", password_hash="h"
    )
    sales1 = User(
        employee_number=2, username="sales1", email="s1@s.com", password_hash="h"
    )
    sales2 = User(
        employee_number=3, username="sales2", email="s2@s.com", password_hash="h"
    )
    support = User(
        employee_number=4, username="support", email="sup@sup.com", password_hash="h"
    )

    db_session.add_all([admin, sales1, sales2, support])
    db_session.commit()

    admin.add_role(role_admin, db_session)
    sales1.add_role(role_sales, db_session)
    sales2.add_role(role_sales, db_session)
    support.add_role(role_support, db_session)
    db_session.commit()

    return {"admin": admin, "sales1": sales1, "sales2": sales2, "support": support}


@pytest.fixture
def controllers(db_session):
    return {
        "user": UserController(session=db_session),
        "client": ClientController(session=db_session),
        "contract": ContractController(session=db_session),
        "event": EventController(session=db_session),
    }


# --- TESTS PERMISSIONS ---


@pytest.mark.as_role("commercial")
def test_sales_cannot_modify_other_sales_client(
    client_ctrl, sales_user, other_sales_client
):
    with pytest.raises(PermissionError, match="Accès refusé"):
        client_ctrl.update_client(other_sales_client.id, {"company_name": "NewCorp"})


def test_support_cannot_access_other_event(controllers, users_with_roles, monkeypatch):
    event_ctrl = controllers["event"]
    contract_ctrl = controllers["contract"]
    client_ctrl = controllers["client"]

    admin, support = users_with_roles["admin"], users_with_roles["support"]

    # En tant qu'admin, créer un client, contrat et event
    monkeypatch.setattr(client_ctrl, "_get_current_user", lambda: admin)
    client = client_ctrl.create_client(
        {
            "full_name": "Client Y",
            "email": "cy@test.com",
            "phone": "0700000000",
            "company_name": "AdminCorp",
        }
    )

    monkeypatch.setattr(contract_ctrl, "_get_current_user", lambda: admin)
    contract = contract_ctrl.create_contract(
        {
            "client_id": client["id"],
            "amount_total": Decimal("1000.00"),
            "amount_due": Decimal("0.00"),
            "is_signed": True,
        }
    )

    monkeypatch.setattr(event_ctrl, "_get_current_user", lambda: admin)
    event = event_ctrl.create_event(
        {
            "contract_id": contract["id"],
            "date_start": datetime.datetime.now() + datetime.timedelta(days=1),
            "date_end": datetime.datetime.now() + datetime.timedelta(days=2),
            "location": "Lyon",
            "attendees": 20,
        }
    )

    # Support tente de voir un event qui ne lui appartient pas
    monkeypatch.setattr(event_ctrl, "_get_current_user", lambda: support)
    with pytest.raises(PermissionError):
        event_ctrl.update_event(event["id"], {"location": "Nice"})


@pytest.mark.as_role("admin")
def test_admin_can_override_all(controllers, users_with_roles, monkeypatch):
    client_ctrl = controllers["client"]
    admin, sales1 = users_with_roles["admin"], users_with_roles["sales1"]

    print("Sales1 roles:", [r.name for r in sales1.roles])
    # sales1 crée un client -> il doit passer avec sales_contact_id = sales1.id
    monkeypatch.setattr(client_ctrl, "_get_current_user", lambda: sales1)
    client = client_ctrl.create_client(
        {
            "full_name": "Client Z",
            "email": "cz@test.com",
            "phone": "0800000000",
            "company_name": "SalesCorp",
            "sales_contact_id": sales1.id,  # important
        }
    )

    # admin reprend la main et modifie le client
    monkeypatch.setattr(client_ctrl, "_get_current_user", lambda: admin)
    updated = client_ctrl.update_client(client["id"], {"company_name": "AdminOverride"})

    assert updated["company_name"] == "AdminOverride"
