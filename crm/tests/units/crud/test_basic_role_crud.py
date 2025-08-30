import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError
from crm.crud.role_crud import RoleCRUD


@pytest.fixture
def crud():
    return RoleCRUD(session=MagicMock())


# ---------- CREATE ----------
def test_create_role_success(crud):
    fake_role = MagicMock()
    with patch("crm.crud.role_crud.Role", return_value=fake_role):
        result = crud.create_role({"name": "manager"})
    crud.session.add.assert_called_once_with(fake_role)
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_role)
    assert result == fake_role


def test_create_role_integrity_error(crud):
    crud.session.add.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with patch("crm.crud.role_crud.Role", return_value=MagicMock()):
        with pytest.raises(IntegrityError):
            crud.create_role({"name": "duplicate"})
    crud.session.rollback.assert_called_once()


def test_create_role_generic_error(crud):
    crud.session.add.side_effect = Exception("boom")
    with patch("crm.crud.role_crud.Role", return_value=MagicMock()):
        with pytest.raises(Exception):
            crud.create_role({"name": "fail"})
    crud.session.rollback.assert_called_once()


# ---------- READ ----------
def test_get_all_calls_get_entities(crud):
    with patch.object(crud, "get_entities", return_value=["r1"]) as mock_get:
        result = crud.get_all()
    assert result == ["r1"]
    mock_get.assert_called_once()


def test_get_by_id(crud):
    with patch("crm.crud.role_crud.Role", autospec=True) as FakeRole:
        crud.session.get.return_value = "role"
        result = crud.get_by_id(1)
        crud.session.get.assert_called_once_with(FakeRole, 1)
        assert result == "role"


def test_find_by_name(crud):
    crud.session.query.return_value.filter_by.return_value.first.return_value = "role"
    result = crud.find_by_name("admin")
    assert result == "role"
    crud.session.query.assert_called_once()


# ---------- UPDATE ----------
def test_update_role_success(crud):
    fake_role = MagicMock()
    crud.session.get.return_value = fake_role
    result = crud.update_role(1, {"name": "updated"})
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_role)
    assert result == fake_role
    assert fake_role.name == "updated"


def test_update_role_not_found(crud):
    crud.session.get.return_value = None
    result = crud.update_role(1, {"name": "x"})
    assert result is None


def test_update_role_integrity_error(crud):
    fake_role = MagicMock()
    crud.session.get.return_value = fake_role
    crud.session.commit.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with pytest.raises(IntegrityError):
        crud.update_role(1, {"name": "dup"})
    crud.session.rollback.assert_called_once()


def test_update_role_generic_error(crud):
    fake_role = MagicMock()
    crud.session.get.return_value = fake_role
    crud.session.commit.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.update_role(1, {"name": "dup"})
    crud.session.rollback.assert_called_once()


# ---------- DELETE ----------
def test_delete_role_success(crud):
    fake_role = MagicMock()
    crud.session.get.return_value = fake_role
    result = crud.delete_role(1)
    crud.session.delete.assert_called_once_with(fake_role)
    crud.session.commit.assert_called_once()
    assert result is True


def test_delete_role_not_found(crud):
    crud.session.get.return_value = None
    result = crud.delete_role(1)
    assert result is False


def test_delete_role_generic_error(crud):
    fake_role = MagicMock()
    crud.session.get.return_value = fake_role
    crud.session.delete.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.delete_role(1)
    crud.session.rollback.assert_called_once()
