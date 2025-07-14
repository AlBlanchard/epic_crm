import datetime as dt
import pytest

from crm.models import Client, User
from sqlalchemy.exc import IntegrityError

from tests.conftest import db_session


def add_user_sales_for_test(db_session):
    """Ajoute un utilisateur de type 'sales' pour les tests."""
    user = User(username="Jean Test", password_hash="hash", role="sales")
    db_session.add(user)
    db_session.flush()
    return user


def add_client_for_test(db_session, user):
    """Ajoute un client pour les tests."""
    if not isinstance(user, User):
        raise ValueError("user must be an instance of User")

    if (user.role == "sales") is False:
        raise ValueError("user must have role 'sales'")

    client = Client(
        full_name="French Connection",
        email="contact@frenchconnection.fr",
        phone="+33123456789",
        company_name="French Connection",
        sales_contact=user,
    )
    db_session.add(client)
    db_session.flush()
    return client


def test_create_valid_client(db_session):
    """Vérifie la création d'un client valide."""
    user = add_user_sales_for_test(db_session)
    db_session.flush()

    client = add_client_for_test(db_session, user)

    db_session.add(client)
    db_session.flush()
    assert client.id is not None
    assert (client.email == "contact@frenchconnection.fr") is True
    assert (client.sales_contact_id == user.id) is True


def test_client_email_cannot_be_unset(db_session):
    """Vérifie qu'un email vide déclenche une erreur SQL (CheckConstraint)."""
    user = add_user_sales_for_test(db_session)
    db_session.add(user)
    db_session.flush()

    with pytest.raises(IntegrityError):
        client = Client(full_name="Error", sales_contact=user)
        db_session.add(client)
        db_session.flush()


def test_client_email_cannot_be_none():
    """Vérifie que le validateur refuse un email None."""
    with pytest.raises(ValueError, match="Email cannot be None"):
        Client(full_name="Test", email=None, sales_contact_id=1)


def test_client_email_invalid_format():
    """Vérifie que le validateur refuse un format invalide."""
    with pytest.raises(ValueError, match="must be a valid email address"):
        Client(full_name="Test", email="invalid-email", sales_contact_id=1)


def test_client_email_must_be_string():
    """Vérifie que le validateur refuse les types non string pour l'email."""
    with pytest.raises(ValueError, match="must be a string"):
        Client(full_name="Test", email=123, sales_contact_id=1)


def test_client_phone_invalid_format():
    """Vérifie que le validateur refuse les numéros incorrects."""
    with pytest.raises(ValueError, match="must be a valid phone number"):
        Client(
            full_name="Test", email="ok@test.com", phone="abc123", sales_contact_id=1
        )


def test_client_missing_sales_contact(db_session):
    """Vérifie qu'un client sans commercial déclenche une erreur."""
    client = Client(full_name="NoContact", email="client@no.fr")
    db_session.add(client)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_client_email_must_be_unique(db_session):
    """Vérifie qu'un email dupliqué déclenche une erreur d'intégrité."""
    user = add_user_sales_for_test(db_session)

    with pytest.raises(IntegrityError):
        db_session.add_all(
            [
                add_client_for_test(db_session, user),
                add_client_for_test(db_session, user),
            ]
        )
        db_session.flush()
