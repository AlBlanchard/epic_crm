import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError
from crm.crud.contract_crud import ContractCRUD


@pytest.fixture
def crud():
    return ContractCRUD(session=MagicMock())


# ---------- CREATE ----------
def test_create_contract_success(crud):
    fake_contract = MagicMock()
    with patch("crm.crud.contract_crud.Contract", return_value=fake_contract):
        result = crud.create({"amount_total": 1000})
    crud.session.add.assert_called_once_with(fake_contract)
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_contract)
    assert result == fake_contract


def test_create_contract_integrity_error(crud):
    crud.session.add.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with patch("crm.crud.contract_crud.Contract", return_value=MagicMock()):
        with pytest.raises(IntegrityError):
            crud.create({"amount_total": 1000})
    crud.session.rollback.assert_called_once()


def test_create_contract_generic_error(crud):
    crud.session.add.side_effect = Exception("boom")
    with patch("crm.crud.contract_crud.Contract", return_value=MagicMock()):
        with pytest.raises(Exception):
            crud.create({"amount_total": 1000})
    crud.session.rollback.assert_called_once()


# ---------- READ ----------
def test_get_all_calls_get_entities(crud):
    with patch.object(crud, "get_entities", return_value=["c1"]) as mock_get:
        result = crud.get_all()
    assert result == ["c1"]
    mock_get.assert_called_once()


def test_get_by_id(crud):
    with patch("crm.crud.contract_crud.Contract", autospec=True) as FakeContract:
        crud.session.get.return_value = "contract"
        result = crud.get_by_id(1)
        crud.session.get.assert_called_once_with(FakeContract, 1)
        assert result == "contract"


def test_get_by_client(crud):
    crud.session.query.return_value.filter_by.return_value.all.return_value = ["c1"]
    result = crud.get_by_client(10)
    assert result == ["c1"]
    crud.session.query.assert_called_once()


def test_get_by_sales_contact(crud):
    fake_query = MagicMock()
    fake_query.options.return_value.filter.return_value.all.return_value = ["c2"]
    crud.session.query.return_value = fake_query

    with patch("crm.crud.contract_crud.selectinload", return_value=MagicMock()):
        # patche aussi Contract.client.sales_contact_id pour le filter
        with patch("crm.crud.contract_crud.Contract") as FakeContract, patch(
            "crm.crud.contract_crud.Client"
        ):
            FakeContract.client.sales_contact_id = MagicMock()

            result = crud.get_by_sales_contact(42)

    assert result == ["c2"]
    fake_query.options.assert_called_once()
    fake_query.options.return_value.filter.assert_called_once()


def test_get_unsigned_contracts(crud):
    with patch.object(crud, "get_all", return_value=["c3"]) as mock_get:
        result = crud.get_unsigned_contracts()
    assert result == ["c3"]
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["filters"]["is_signed"] is False


def test_get_unsigned_contracts_with_sales_contact(crud):
    with patch.object(crud, "get_all", return_value=["c3"]) as mock_get:
        result = crud.get_unsigned_contracts(sales_contact_id=99)
    assert result == ["c3"]
    args, kwargs = mock_get.call_args
    assert kwargs["filters"]["sales_contact_id"] == 99


# ---------- UPDATE ----------
def test_update_contract_success(crud):
    fake_contract = MagicMock()
    crud.session.get.return_value = fake_contract
    result = crud.update(1, {"amount_total": 2000})
    crud.session.commit.assert_called_once()
    crud.session.refresh.assert_called_once_with(fake_contract)
    assert result == fake_contract
    assert fake_contract.amount_total == 2000


def test_update_contract_not_found(crud):
    crud.session.get.return_value = None
    result = crud.update(1, {"amount_total": 2000})
    assert result is None


def test_update_contract_integrity_error(crud):
    fake_contract = MagicMock()
    crud.session.get.return_value = fake_contract
    crud.session.commit.side_effect = IntegrityError("stmt", "params", "orig")  # type: ignore
    with pytest.raises(IntegrityError):
        crud.update(1, {"amount_total": 2000})
    crud.session.rollback.assert_called_once()


def test_update_contract_generic_error(crud):
    fake_contract = MagicMock()
    crud.session.get.return_value = fake_contract
    crud.session.commit.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.update(1, {"amount_total": 2000})
    crud.session.rollback.assert_called_once()


# ---------- DELETE ----------
def test_delete_contract_success(crud):
    fake_contract = MagicMock()
    crud.session.get.return_value = fake_contract
    result = crud.delete(1)
    crud.session.delete.assert_called_once_with(fake_contract)
    crud.session.commit.assert_called_once()
    assert result is True


def test_delete_contract_not_found(crud):
    crud.session.get.return_value = None
    result = crud.delete(1)
    assert result is False


def test_delete_contract_generic_error(crud):
    fake_contract = MagicMock()
    crud.session.get.return_value = fake_contract
    crud.session.delete.side_effect = Exception("boom")
    with pytest.raises(Exception):
        crud.delete(1)
    crud.session.rollback.assert_called_once()


# ---------- UTILS ----------
def test_contract_has_events_true(crud):
    fake_contract = MagicMock(event=["ev1"])
    crud.session.get.return_value = fake_contract
    assert crud.contract_has_events(1) is True


def test_contract_has_events_false(crud):
    fake_contract = MagicMock(event=[])
    crud.session.get.return_value = fake_contract
    assert crud.contract_has_events(1) is False


def test_contract_has_events_not_found(crud):
    crud.session.get.return_value = None
    assert crud.contract_has_events(1) is False
