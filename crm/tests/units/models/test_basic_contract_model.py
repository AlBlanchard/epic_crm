import pytest
from decimal import Decimal
from crm.models.contract import Contract
from crm.models.client import Client
from crm.models.user import User


@pytest.fixture
def fake_user():
    u = User()
    u.id = 1
    u.username = "jean"
    return u


@pytest.fixture
def fake_client(fake_user):
    c = Client()
    c.id = 10
    c.full_name = "Agence Est"
    c.sales_contact = fake_user
    c.sales_contact_id = fake_user.id
    return c


def test_repr_basic():
    c = Contract()
    c.id = 1
    c.amount_total = Decimal("100.00")
    c.is_signed = True
    assert repr(c) == "<Contract(id=1, total=100.00, signed=True)>"


def test_client_name(fake_client):
    contract = Contract()
    contract.client = fake_client
    assert contract.client_name == "Agence Est"


def test_sales_contact_name_with_user(fake_client):
    contract = Contract()
    contract.client = fake_client
    assert contract.sales_contact_name == "jean"


def test_sales_contact_name_no_user():
    contract = Contract()
    contract.client = Client()
    contract.client.sales_contact = None
    assert contract.sales_contact_name == "Aucun contact"


def test_sales_contact_id(fake_client):
    contract = Contract()
    contract.client = fake_client
    assert contract.sales_contact_id == 1


def test_is_payed_true():
    c = Contract()
    c.amount_due = Decimal("0.00")
    assert c.is_payed is True


def test_is_payed_false():
    c = Contract()
    c.amount_due = Decimal("10.00")
    assert c.is_payed is False


# -------- VALIDATIONS --------


def test_validate_amount_total_must_be_positive():
    c = Contract()
    with pytest.raises(ValueError):
        c.validate_amounts("amount_total", Decimal("-5"))


def test_validate_amount_total_zero_invalid():
    c = Contract()
    with pytest.raises(ValueError):
        c.validate_amounts("amount_total", Decimal("0"))


def test_validate_amount_due_cannot_exceed_total():
    c = Contract()
    c.amount_total = Decimal("100.00")
    with pytest.raises(ValueError):
        c.validate_amounts("amount_due", Decimal("150.00"))


def test_validate_amount_total_less_than_due_invalid():
    c = Contract()
    c.amount_due = Decimal("200.00")
    with pytest.raises(ValueError):
        c.validate_amounts("amount_total", Decimal("100.00"))


def test_validate_amounts_accepts_int_and_float():
    c = Contract()
    assert isinstance(c.validate_amounts("amount_total", 100), Decimal)
    assert isinstance(c.validate_amounts("amount_due", 50.5), Decimal)


def test_validate_amounts_invalid_type():
    c = Contract()
    with pytest.raises(ValueError):
        c.validate_amounts("amount_total", "not-a-number")
