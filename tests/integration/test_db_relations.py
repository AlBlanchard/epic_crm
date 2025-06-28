import datetime as dt
import pytest
from decimal import Decimal

from crm.models import User, Client, Contract, Event
from sqlalchemy.exc import IntegrityError


# ---------- FK obligatoire client -> user ------------------------------
def test_client_requires_sales_contact(db_session):
    # Pas de commercial : doit échouer (sales_contact_id NULL + FK NOT NULL)
    client = Client(full_name="NoRep", email="norep@example.com")
    db_session.add(client)

    with pytest.raises(IntegrityError):
        db_session.flush()


# ------------ UNIQUE 1 to 1 event <-> contract ------------------------
def test_event_unique_per_contract(db_session):
    sales = User(username="sales1", password_hash="pwd", role="sales")
    client = Client(full_name="Foo", email="foo@bar", sales_contact=sales)
    contract = Contract(
        client=client,
        sales_contact=sales,
        amount_total=Decimal("1000.00"),
        amount_due=0,
        is_signed=True,
    )
    first_event = Event(
        contract=contract,
        date_start=dt.date.today(),
        date_end=dt.date.today(),
        location="Paris",
    )

    db_session.add_all([sales, client, contract, first_event])
    db_session.commit()

    # 2eme événement pour le même contrat : doit violer la contrainte UNIQUE
    second_event = Event(
        contract=contract,
        date_start=dt.date.today(),
        date_end=dt.date.today(),
        location="Lyon",
    )
    db_session.add(second_event)

    with pytest.raises(IntegrityError):
        db_session.commit()


# --------- Cascade logique many-to-one --------------------------
def test_contract_linked_to_client_and_user(db_session):
    sales = User(username="alice", password_hash="***", role="sales")
    client = Client(full_name="ACME", email="acme@corp", sales_contact=sales)
    contract = Contract(
        client=client,
        sales_contact=sales,
        amount_total=10,
        amount_due=0,
        is_signed=True,
    )

    db_session.add_all([sales, client, contract])
    db_session.commit()

    # Vérifie que la FK a bien été matérialisée
    result = db_session.query(Contract).filter_by(id=contract.id).first()
    assert result.client.full_name == "ACME"
    assert result.sales_contact.username == "alice"
