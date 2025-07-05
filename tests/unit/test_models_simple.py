import datetime as dt
from decimal import Decimal

from crm.models import User, Client, Contract, Event


def test_user_repr_and_defaults():
    """Test la représentation de l'utilisateur et les valeurs par défaut."""
    user = User(username="testuser", password_hash="hash", role="sales")
    assert "<User(" in repr(user)
    assert user.clients == []


def test_client_defaults_dates():
    fake_now = dt.datetime.now(dt.timezone.utc)
    # On passe un faux commercial
    sales = User(username="Lucile", password_hash="hash", role="sales")
    client = Client(full_name="Macif", email="contact@macif.fr", sales_contact=sales)

    assert isinstance(client.first_contact, dt.datetime)
    assert (client.first_contact - fake_now).total_seconds() < 5


def test_contract_amount_due_cannot_exceed_total():
    sales = User(username="Lohan", password_hash="hash", role="sales")
    client = Client(full_name="Préfecture", email="pref@gouv.fr", sales_contact=sales)
    contract = Contract(
        client=client,
        sales_contract=sales,
        amount_total=Decimal("1000.00"),
        amount_due=Decimal("1200.00"),
        is_signed=False,
    )
