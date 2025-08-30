import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError
from crm.crud.user_crud import UserCRUD


@pytest.fixture
def crud():
    return UserCRUD(session=MagicMock())


# ---------- CREATE ----------
def test_create_user_success(crud):
    user_data = {"username": "jean", "email": "j@test.com"}
    fake_user = MagicMock()
    with patch("crm.crud.user_crud.User", return_value=fake_user):
        result = crud.create_user(user_data)
    crud.session.add.assert_called_once_with(fake_user)
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_user)
    assert result == fake_user


def test_create_user_with_password(crud):
    user_data = {"username": "jean", "password": "secret"}
    fake_user = MagicMock()
    with patch("crm.crud.user_crud.User", return_value=fake_user):
        crud.create_user(user_data)
    fake_user.set_password.assert_called_once_with("secret")


def test_create_user_integrity_error(crud):
    crud.session.add.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with patch("crm.crud.user_crud.User", return_value=MagicMock()):
        with pytest.raises(ValueError):
            crud.create_user({"username": "jean"})
    crud.session.rollback.assert_called_once()


def test_create_user_generic_error(crud):
    crud.session.add.side_effect = Exception("boom")
    with patch("crm.crud.user_crud.User", return_value=MagicMock()):
        with pytest.raises(ValueError):
            crud.create_user({"username": "jean"})
    crud.session.rollback.assert_called_once()


# ---------- READ ----------
def test_get_all_calls_get_entities(crud):
    with patch.object(crud, "get_entities", return_value=["u1"]) as mock_get:
        result = crud.get_all()
    assert result == ["u1"]
    mock_get.assert_called_once()


def test_get_by_id(crud):
    with patch("crm.crud.user_crud.User", autospec=True) as FakeUser:
        crud.session.get.return_value = "user"
        result = crud.get_by_id(1)
        crud.session.get.assert_called_once_with(FakeUser, 1)
        assert result == "user"


# ---------- UPDATE ----------
def test_update_user_success(crud):
    fake_user = MagicMock()
    crud.session.get.return_value = fake_user
    result = crud.update_user(1, {"username": "new"})
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_user)
    assert result == fake_user


def test_update_user_with_password(crud):
    fake_user = MagicMock()
    crud.session.get.return_value = fake_user
    crud.update_user(1, {"password": "newpwd"})
    fake_user.set_password.assert_called_once_with("newpwd")


def test_update_user_not_found(crud):
    crud.session.get.return_value = None
    result = crud.update_user(1, {"username": "x"})
    assert result is None


def test_update_user_integrity_error(crud):
    fake_user = MagicMock()
    crud.session.get.return_value = fake_user
    crud.session.commit.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with pytest.raises(ValueError):
        crud.update_user(1, {"username": "x"})
    crud.session.rollback.assert_called_once()


def test_update_user_generic_error(crud):
    fake_user = MagicMock()
    crud.session.get.return_value = fake_user
    crud.session.commit.side_effect = Exception("boom")
    with pytest.raises(ValueError):
        crud.update_user(1, {"username": "x"})
    crud.session.rollback.assert_called_once()


def test_update_password_success(crud):
    fake_user = MagicMock()
    crud.session.get.return_value = fake_user
    result = crud.update_password(1, "pwd")
    assert result is True
    fake_user.set_password.assert_called_once_with("pwd")


def test_update_password_not_found(crud):
    crud.session.get.return_value = None
    result = crud.update_password(1, "pwd")
    assert result is False


def test_update_password_generic_error(crud):
    fake_user = MagicMock()
    crud.session.get.return_value = fake_user
    crud.session.commit.side_effect = Exception("boom")
    with pytest.raises(ValueError):
        crud.update_password(1, "pwd")
    crud.session.rollback.assert_called_once()


# ---------- DELETE ----------
def test_delete_user_success(crud):
    fake_user = MagicMock()
    crud.session.get.return_value = fake_user
    result = crud.delete_user(1)
    crud.session.delete.assert_called_once_with(fake_user)
    crud.session.commit.assert_called_once()
    assert result is True


def test_delete_user_not_found(crud):
    crud.session.get.return_value = None
    result = crud.delete_user(1)
    assert result is False


def test_delete_user_generic_error(crud):
    fake_user = MagicMock()
    crud.session.get.return_value = fake_user
    crud.session.delete.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.delete_user(1)
    crud.session.rollback.assert_called_once()


# ---------- ROLES ----------
def test_add_role_to_user_success(crud):
    crud.user_has_role_by_id = MagicMock(return_value=False)
    result = crud.add_role_to_user(1, 2)
    crud.session.add.assert_called_once()
    crud.session.commit.assert_called_once()
    assert result is True


def test_add_role_to_user_already_exists(crud):
    crud.user_has_role_by_id = MagicMock(return_value=True)
    result = crud.add_role_to_user(1, 2)
    assert result is False


def test_add_role_to_user_integrity_error(crud):
    crud.user_has_role_by_id = MagicMock(return_value=False)
    crud.session.add.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    result = crud.add_role_to_user(1, 2)
    assert result is False
    crud.session.rollback.assert_called_once()


def test_add_role_to_user_generic_error(crud):
    crud.user_has_role_by_id = MagicMock(return_value=False)
    crud.session.add.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.add_role_to_user(1, 2)
    crud.session.rollback.assert_called_once()


def test_remove_role_from_user_success(crud):
    fake_role = MagicMock()
    crud.session.query.return_value.filter_by.return_value.first.return_value = (
        fake_role
    )
    result = crud.remove_role_from_user(1, 2)
    crud.session.delete.assert_called_once_with(fake_role)
    crud.session.commit.assert_called_once()
    assert result is True


def test_remove_role_from_user_not_found(crud):
    crud.session.query.return_value.filter_by.return_value.first.return_value = None
    result = crud.remove_role_from_user(1, 2)
    assert result is False


def test_remove_role_from_user_generic_error(crud):
    fake_role = MagicMock()
    crud.session.query.return_value.filter_by.return_value.first.return_value = (
        fake_role
    )
    crud.session.delete.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.remove_role_from_user(1, 2)
    crud.session.rollback.assert_called_once()


def test_get_user_roles(crud):
    crud.session.query.return_value.join.return_value.filter.return_value.all.return_value = [
        "role"
    ]
    result = crud.get_user_roles(1)
    assert result == ["role"]


def test_user_has_role_by_id_true(crud):
    crud.session.query.return_value.filter_by.return_value.first.return_value = (
        "user_role"
    )
    result = crud.user_has_role_by_id(1, 2)
    assert result is True


def test_user_has_role_by_id_false(crud):
    crud.session.query.return_value.filter_by.return_value.first.return_value = None
    result = crud.user_has_role_by_id(1, 2)
    assert result is False


def test_user_has_role_by_name_true(crud):
    crud.session.query.return_value.join.return_value.filter.return_value.first.return_value = (
        "role"
    )
    result = crud.user_has_role_by_name(1, "admin")
    assert result is True


def test_user_has_role_by_name_false(crud):
    crud.session.query.return_value.join.return_value.filter.return_value.first.return_value = (
        None
    )
    result = crud.user_has_role_by_name(1, "admin")
    assert result is False
