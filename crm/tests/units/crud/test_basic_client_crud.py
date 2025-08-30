import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError
from crm.crud.client_crud import ClientCRUD


@pytest.fixture
def crud():
    return ClientCRUD(session=MagicMock())


# ---------- CREATE ----------
def test_create_client_success(crud):
    fake_client = MagicMock()
    with patch("crm.crud.client_crud.Client", return_value=fake_client):
        result = crud.create_client({"company_name": "TestCorp"})
    crud.session.add.assert_called_once_with(fake_client)
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_client)
    assert result == fake_client


def test_create_client_integrity_error(crud):
    crud.session.add.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with patch("crm.crud.client_crud.Client", return_value=MagicMock()):
        with pytest.raises(IntegrityError):
            crud.create_client({"company_name": "X"})
    crud.session.rollback.assert_called_once()


def test_create_client_generic_error(crud):
    crud.session.add.side_effect = Exception("boom")
    with patch("crm.crud.client_crud.Client", return_value=MagicMock()):
        with pytest.raises(Exception):
            crud.create_client({"company_name": "X"})
    crud.session.rollback.assert_called_once()


# ---------- READ ----------
def test_get_all_calls_get_entities(crud):
    with patch.object(crud, "get_entities", return_value=["c1"]) as mock_get:
        result = crud.get_all()
    assert result == ["c1"]
    mock_get.assert_called_once()


def test_get_by_id(crud):
    with patch("crm.crud.client_crud.Client", autospec=True) as FakeClient:
        crud.session.get.return_value = "client"
        result = crud.get_by_id(1)
        crud.session.get.assert_called_once_with(FakeClient, 1)
        assert result == "client"


def test_get_clients_by_sales_contact(crud):
    crud.session.query.return_value.filter_by.return_value.all.return_value = ["c1"]
    result = crud.get_clients_by_sales_contact(42)
    assert result == ["c1"]
    crud.session.query.assert_called_once()


# ---------- UPDATE ----------
def test_update_client_success(crud):
    fake_client = MagicMock()
    crud.session.get.return_value = fake_client
    result = crud.update_client(1, {"company_name": "NewCorp"})
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_client)
    assert result == fake_client
    assert fake_client.company_name == "NewCorp"


def test_update_client_not_found(crud):
    crud.session.get.return_value = None
    result = crud.update_client(1, {"company_name": "NewCorp"})
    assert result is None


def test_update_client_integrity_error(crud):
    fake_client = MagicMock()
    crud.session.get.return_value = fake_client
    crud.session.commit.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with pytest.raises(IntegrityError):
        crud.update_client(1, {"company_name": "X"})
    crud.session.rollback.assert_called_once()


def test_update_client_generic_error(crud):
    fake_client = MagicMock()
    crud.session.get.return_value = fake_client
    crud.session.commit.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.update_client(1, {"company_name": "X"})
    crud.session.rollback.assert_called_once()


def test_assign_sales_contact_success(crud):
    fake_client = MagicMock()
    crud.session.get.return_value = fake_client
    result = crud.assign_sales_contact(1, 99)
    assert result is True
    assert fake_client.sales_contact_id == 99
    crud.session.commit.assert_called_once()


def test_assign_sales_contact_not_found(crud):
    crud.session.get.return_value = None
    result = crud.assign_sales_contact(1, 99)
    assert result is False


def test_assign_sales_contact_generic_error(crud):
    fake_client = MagicMock()
    crud.session.get.return_value = fake_client
    crud.session.commit.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.assign_sales_contact(1, 99)
    crud.session.rollback.assert_called_once()


# ---------- DELETE ----------
def test_delete_client_success(crud):
    fake_client = MagicMock()
    crud.session.get.return_value = fake_client
    result = crud.delete_client(1)
    crud.session.delete.assert_called_once_with(fake_client)
    crud.session.commit.assert_called_once()
    assert result is True


def test_delete_client_not_found(crud):
    crud.session.get.return_value = None
    result = crud.delete_client(1)
    assert result is False


def test_delete_client_generic_error(crud):
    fake_client = MagicMock()
    crud.session.get.return_value = fake_client
    crud.session.delete.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.delete_client(1)
    crud.session.rollback.assert_called_once()


# ---------- UTILS ----------
def test_client_has_contracts_true(crud):
    fake_client = MagicMock(contracts=["contract"])
    crud.session.get.return_value = fake_client
    assert crud.client_has_contracts(1) is True


def test_client_has_contracts_false(crud):
    fake_client = MagicMock(contracts=[])
    crud.session.get.return_value = fake_client
    assert crud.client_has_contracts(1) is False


def test_client_has_contracts_not_found(crud):
    crud.session.get.return_value = None
    assert crud.client_has_contracts(1) is False
