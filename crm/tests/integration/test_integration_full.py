import pytest
import datetime
from decimal import Decimal

from crm.controllers.user_controller import UserController
from crm.controllers.client_controller import ClientController
from crm.controllers.contract_controller import ContractController
from crm.controllers.event_controller import EventController
from crm.models.role import Role
from crm.models.user import User
from crm.crud.client_crud import ClientCRUD


@pytest.fixture
def controllers(db_session, monkeypatch):
    user_ctrl = UserController(session=db_session)
    client_ctrl = ClientController(session=db_session)
    contract_ctrl = ContractController(session=db_session)
    event_ctrl = EventController(session=db_session)

    # Crée un admin
    admin = User(
        employee_number=99,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
    )
    role_admin = Role(name="admin")
    db_session.add_all([admin, role_admin])
    db_session.commit()
    admin.add_role(role_admin, db_session)
    db_session.commit()

    # Monkeypatch pour toujours agir en tant qu’admin
    for ctrl in (user_ctrl, client_ctrl, contract_ctrl, event_ctrl):
        monkeypatch.setattr(ctrl, "_get_current_user", lambda: admin)

    return user_ctrl, client_ctrl, contract_ctrl, event_ctrl, admin


def test_full_sales_workflow(controllers):
    user_ctrl, client_ctrl, contract_ctrl, event_ctrl, admin = controllers

    # Crée un user sales
    sales = user_ctrl.create_user(
        {
            "username": "salesman",
            "email": "sales@test.com",
            "employee_number": 1234,
            "password": "secret",
        }
    )
    assert sales["username"] == "salesman"

    # Crée un client
    client = client_ctrl.create_client(
        {
            "full_name": "Client Intégration",
            "email": "client@test.com",
            "phone": "0601020304",
            "company_name": "TestCo",
            "sales_contact_id": sales["id"],
        }
    )
    assert client["company_name"] == "TestCo"

    # Crée un contrat
    contract = contract_ctrl.create_contract(
        {
            "client_id": client["id"],
            "amount_total": Decimal("1000.00"),
            "amount_due": Decimal("500.00"),
            "is_signed": True,
        }
    )
    assert contract["is_signed"] is True

    # Crée un event
    event = event_ctrl.create_event(
        {
            "contract_id": contract["id"],
            "date_start": datetime.datetime.now() + datetime.timedelta(days=1),
            "date_end": datetime.datetime.now() + datetime.timedelta(days=2),
            "location": "Paris",
            "attendees": 10,
        }
    )
    assert event["location"] == "Paris"

    # 5. Ajouter une note
    event_ctrl.create_note(event["id"], "Préparer la salle")
    notes = event_ctrl.list_event_notes(event["id"])
    assert any("Préparer la salle" in n["note"] for n in notes)
