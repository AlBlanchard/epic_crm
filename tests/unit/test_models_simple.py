import datetime as dt
from decimal import Decimal

import datetime
import pytest

from crm.models import User, Client, Contract, Event


# ---------- User --------------------------------------------------------------- #
def test_user_init_defaults():
    u = User(username="alice", password_hash="hash", role="sales")

    assert u.id is None  # pas encore persisté
    assert getattr(u, "username", None) == "alice"
    assert getattr(u, "role", None) == "sales"
    assert u.clients == []  # liste vide par défaut
    assert repr(u).startswith("<User(")


# ----------- Client ----------------------------------------------------------- #
def test_client_defaults_and_sales_link(db_session):
    sales = User(username="bob", password_hash="123", role="sales")
    client = Client(full_name="ACME Corp", email="info@acme.io", sales_contact=sales)
    db_session.add_all([sales, client])
    db_session.commit()

    assert client.first_contact is not None


# ------------ Contract ------------------------------------------------------ #
def test_contract_amounts_and_links():
    sales = User(username="carol", password_hash="***", role="sales")
    client = Client(full_name="Foo", email="foo@bar.io", sales_contact=sales)

    contract = Contract(
        client=client,
        sales_contact=sales,
        amount_total=Decimal("5000.00"),
        amount_due=Decimal("2000.00"),
        is_signed=True,
    )

    assert contract.client is client
    assert contract.sales_contact is sales
    assert getattr(contract, "amount_total", None) == Decimal("5000.00")
    assert contract.is_signed is True
    assert repr(contract).startswith("<Contract(")


# ---------- Event -------------------------------------------------------------- #
def test_event_one_to_one_contract_link():
    contract = Contract(
        client=Client(full_name="X", email="x@y.z"),
        sales_contact=User(username="dave", password_hash="***", role="sales"),
        amount_total=100,
        amount_due=0,
        is_signed=True,
    )
    support = User(username="eva", password_hash="***", role="support")

    event = Event(
        contract=contract,
        support_contact=support,
        date_start=dt.date(2025, 1, 1),
        date_end=dt.date(2025, 1, 2),
        location="Paris",
        attendees=50,
    )

    assert event.contract is contract
    assert contract.event is event  # lien 1↔1 en mémoire
    assert event.support_contact.username == "eva"
    assert getattr(event, "attendees", None) == 50
