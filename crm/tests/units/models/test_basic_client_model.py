import pytest
from crm.models.client import Client
from crm.models.user import User


@pytest.fixture
def fake_user():
    u = User()
    u.id = 1
    u.username = "jean"
    return u


def test_repr_basic():
    c = Client()
    c.id = 42
    c.full_name = "Agence Est"
    assert repr(c) == "<Client(id=42, name='Agence Est')>"


def test_sales_contact_name_none():
    c = Client()
    c.full_name = "Agence Est"
    c.sales_contact = None
    assert c.sales_contact_name == "Aucun contact"


def test_sales_contact_name_with_user(fake_user):
    c = Client()
    c.full_name = "Agence Est"
    c.sales_contact = fake_user
    assert c.sales_contact_name == "jean"


def test_is_assigned_true(fake_user):
    c = Client()
    c.sales_contact = fake_user
    assert c.is_assigned is True


def test_is_assigned_false():
    c = Client()
    c.sales_contact = None
    assert c.is_assigned is False


def test_validate_email_valid():
    c = Client()
    assert c.validate_email("email", "client@example.com") == "client@example.com"


def test_validate_email_invalid():
    c = Client()
    with pytest.raises(ValueError):
        c.validate_email("email", "invalid-email")


def test_validate_phone_valid():
    c = Client()
    assert c.validate_phone("phone", "0123456789") == "0123456789"


def test_validate_phone_invalid():
    c = Client()
    with pytest.raises(ValueError):
        c.validate_phone("phone", "not-a-phone")
