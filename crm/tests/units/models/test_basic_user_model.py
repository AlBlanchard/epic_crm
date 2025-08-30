import pytest
from unittest.mock import MagicMock

from crm.models.user import User
from crm.models.role import Role
from crm.models.user_role import UserRole


@pytest.fixture
def fake_session():
    return MagicMock()


@pytest.fixture
def fake_role():
    r = Role()
    r.id = 1
    r.name = "admin"
    return r


def test_validate_employee_number_valid():
    user = User()
    assert user.validate_employee_number("employee_number", 1234567890) == 1234567890


def test_validate_employee_number_invalid():
    user = User()
    with pytest.raises(ValueError):
        user.validate_employee_number("employee_number", 99999999999)  # 11 chiffres


def test_set_password_and_verify_ok():
    user = User()
    user.set_password("secret123")
    assert user.password_hash is not None
    assert user.verify_password("secret123") is True


def test_set_password_invalid():
    user = User()
    with pytest.raises(ValueError):
        user.set_password("")  # mot de passe vide


def test_verify_password_wrong():
    user = User()
    user.set_password("secret123")
    assert user.verify_password("wrongpass") is False


def test_roles_and_has_role(fake_role):
    user = User()
    ur = UserRole(user=user, role=fake_role)
    ur.role_id = fake_role.id  # clé manquante
    user.user_roles.append(ur)

    assert fake_role in user.roles
    assert user.has_role(fake_role) is True


def test_add_role_success(fake_session, fake_role):
    user = User()
    user.username = "alice"
    user.user_roles = []

    user.add_role(fake_role, fake_session)

    fake_session.add.assert_called_once()
    fake_session.flush.assert_called_once()


def test_add_role_duplicate(fake_session, fake_role):
    user = User()
    user.username = "tealc"
    ur = UserRole(user=None, role=fake_role)
    ur.role_id = fake_role.id  # indispensable
    user.user_roles = [ur]

    with pytest.raises(ValueError):
        user.add_role(fake_role, fake_session)


def test_remove_role_success(fake_session, fake_role):
    user = User()
    user.username = "charlie"
    ur = UserRole(user=user, role=fake_role)
    ur.role_id = fake_role.id
    user.user_roles = [ur]

    user.remove_role(fake_role, fake_session)

    fake_session.delete.assert_called_once_with(ur)
    fake_session.flush.assert_called_once()


def test_remove_role_not_found(fake_session, fake_role):
    user = User()
    user.username = "dave"
    user.user_roles = []

    with pytest.raises(ValueError):
        user.remove_role(fake_role, fake_session)


def test_repr_contains_username_and_roles(fake_role):
    user = User()
    user.id = 1
    user.username = "eva"
    user.employee_number = 123
    ur = UserRole(user=user, role=fake_role)
    ur.role_id = fake_role.id
    user.user_roles = [ur]

    text = repr(user)
    assert "eva" in text
    assert "admin" in text
