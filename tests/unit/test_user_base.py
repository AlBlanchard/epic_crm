import datetime as dt
import pytest

from crm.models import User
from sqlalchemy.exc import IntegrityError

from tests.conftest import db_session


def test_create_user_valid(db_session):
    """Test la création d'un utilisateur avec des données valides."""
    user = User(username="Francis", password_hash="hash", role="sales")
    db_session.add(user)
    db_session.flush()

    assert user.id is not None
    assert (user.username == "Francis") is True
    assert (user.role == "sales") is True
    assert isinstance(user.created_at, dt.datetime)
    assert isinstance(user.updated_at, dt.datetime)


def test_create_user_without_username_fail(db_session):
    """Test la création d'un utilisateur sans nom d'utilisateur."""
    user = User(password_hash="hash", role="sales")
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_create_user_without_password_fail(db_session):
    """Test la création d'un utilisateur sans mot de passe."""
    user = User(username="Francis", role="sales")
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_create_user_without_role_fail(db_session):
    """Test la création d'un utilisateur sans rôle."""
    user = User(username="Francis", password_hash="hash")
    db_session.add(user)

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_create_user_with_invalid_role_fail(db_session):
    """Test la création d'un utilisateur avec un rôle invalide."""

    # Ici j'ai dû créer l'utilisateur dans le pytest.raises
    # car sinon la ligne db_session.add(user) n'est jamais atteinte
    # donc l'exception n'est pas levée au bon endroit.
    with pytest.raises(
        ValueError, match="Invalid role 'invalid_role'. Must be one of:"
    ):
        user = User(username="Francis", password_hash="hash", role="invalid_role")
        db_session.add(user)
        db_session.flush()


def test_create_user_with_duplicate_username_fail(db_session, sample_users):
    """Test la création d'un utilisateur avec un nom d'utilisateur déjà existant."""
    user = User(username="User double", password_hash="hash", role="sales")
    db_session.add(user)
    user_double = User(username="User double", password_hash="hash", role="sales")
    db_session.add(user_double)

    with pytest.raises(IntegrityError):
        db_session.flush()
