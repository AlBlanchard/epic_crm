import datetime as dt
import pytest

from crm.models import User
from sqlalchemy.exc import IntegrityError

from tests.conftest import db_session


def test_create_user_valid(db_session, sales_dept):
    """Test la création d'un utilisateur avec des données valides."""
    user = User(
        employee_number=123,
        username="Francis",
        email="francis@test.com",
        department=sales_dept,
    )
    user.set_password("FrancisTheKing123")  # hash argon2
    db_session.add(user)
    db_session.flush()

    # Champs de base
    assert user.id is not None
    assert (user.username == "Francis") is True
    assert user.department == sales_dept
    # Mot de passe haché différent du brut
    assert (user.password_hash != "FrancisTheKing123") is True
    assert user.verify_password("FrancisTheKing123") is True
    # Timestamps
    assert isinstance(user.created_at, dt.datetime)
    assert isinstance(user.updated_at, dt.datetime)


def test_user_without_username_fails(db_session, sales_dept):
    """Test la création d'un utilisateur sans nom d'utilisateur."""
    user = User(
        employee_number=124,
        email="no_user@test.com",
        department=sales_dept,
    )
    user.set_password("pwd")
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_without_password_fails(db_session, sales_dept):
    """Test la création d'un utilisateur sans mot de passe."""
    user = User(
        employee_number=125,
        username="nopwd",
        email="nopwd@test.com",
        department=sales_dept,
    )
    # on n'appelle pas set_password
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_user_without_department_fails(db_session):
    """Test la création d'un utilisateur sans département."""
    user = User(
        employee_number=126,
        username="nodept",
        email="nodept@test.com",
    )
    user.set_password("pwd")
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_create_user_with_invalid_role_fail(db_session):
    """Test la création d'un utilisateur avec un rôle invalide."""

    # Ici j'ai dû créer l'utilisateur dans le pytest.raises
    # car sinon la ligne db_session.add(user) n'est jamais atteinte
    # donc l'exception n'est pas levée au bon endroit.
    with pytest.raises(IntegrityError):
        user = User(
            employee_number=127,
            username="baddept",
            email="bad@dept.com",
            department_id=9999,
        )
        user.set_password("pwd")
        db_session.add(user)
        db_session.flush()


def test_create_user_with_duplicate_username_fail(db_session, sales_dept):
    """Test la création d'un utilisateur avec un nom d'utilisateur déjà existant."""
    user1 = User(
        employee_number=128,
        username="The Duke",
        email="duke1@test.com",
        department=sales_dept,
    )
    user1.set_password("pwd")
    user2 = User(
        employee_number=129,
        username="The Duke",
        email="duke2@test.com",
        department=sales_dept,
    )
    user2.set_password("pwd")

    db_session.add_all([user1, user2])

    with pytest.raises(IntegrityError):
        db_session.flush()
