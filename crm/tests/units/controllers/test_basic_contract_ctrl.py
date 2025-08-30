import pytest
from unittest.mock import MagicMock, patch
from crm.controllers.contract_controller import ContractController


@pytest.fixture
def controller():
    ctrl = ContractController(session=MagicMock())
    ctrl._setup_services()
    ctrl.contracts = MagicMock()
    ctrl.clients = MagicMock()
    ctrl.users = MagicMock()
    ctrl.serializer = MagicMock()
    ctrl._get_current_user = MagicMock(return_value=MagicMock(id=1))
    return ctrl


def fake_selectinload(*args, **kwargs):
    m = MagicMock()
    m.selectinload.return_value = m  # permet de chaîner les appels
    return m


# ---------- list_all ----------
def test_list_all_success(controller):
    fake_contract = MagicMock(id=1)
    controller.contracts.get_all.return_value = [fake_contract]
    controller.serializer.serialize_list.return_value = [{"id": 1}]

    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):
        result = controller.list_all()

    assert result == [{"id": 1}]
    controller.contracts.get_all.assert_called_once()


def test_list_all_no_permission(controller):
    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.list_all()


# ---------- get_contract ----------
def test_get_contract_success(controller):
    fake_contract = MagicMock(id=2, client=MagicMock(sales_contact_id=1))
    controller.contracts.get_by_id.return_value = fake_contract
    controller.serializer.serialize.return_value = {"id": 2}

    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ), patch.object(controller, "_ensure_owner_or_admin", return_value=True):
        result = controller.get_contract(2)

    assert result == {"id": 2}


def test_get_contract_not_found(controller):
    controller.contracts.get_by_id.return_value = None
    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.get_contract(999)


def test_get_contract_no_permission(controller):
    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.get_contract(1)


# ---------- is_contract_signed ----------
def test_is_contract_signed_true(controller):
    fake_contract = MagicMock(is_signed=True)
    controller.contracts.get_by_id.return_value = fake_contract
    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):
        assert controller.is_contract_signed(1) is True


def test_is_contract_signed_not_found(controller):
    controller.contracts.get_by_id.return_value = None
    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.is_contract_signed(999)


# ---------- list_unsigned_contracts / signed ----------
def test_list_unsigned_contracts_success(controller):
    fake_contract = MagicMock(id=1)
    controller.contracts.get_all.return_value = [fake_contract]
    controller.serializer.serialize_list.return_value = [{"id": 1}]

    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):
        result = controller.list_unsigned_contracts(signed=False)

    assert result == [{"id": 1}]


def test_list_signed_contracts_success(controller):
    fake_contract = MagicMock(id=2)
    controller.contracts.get_all.return_value = [fake_contract]
    controller.serializer.serialize_list.return_value = [{"id": 2}]

    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):
        result = controller.list_signed_contracts()

    assert result == [{"id": 2}]


# ---------- get_contract_owner ----------
def test_get_contract_owner_success(controller):
    fake_owner = MagicMock(id=99)
    fake_client = MagicMock(sales_contact=fake_owner)
    fake_contract = MagicMock(client=fake_client)

    with patch(
        "crm.controllers.contract_controller.selectinload",
        side_effect=fake_selectinload,
    ), patch.object(controller.session, "get", return_value=fake_contract), patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):

        result = controller.get_contract_owner(1)

    assert result == fake_owner


def test_get_contract_owner_no_client(controller):
    fake_contract = MagicMock(client=None)

    with patch(
        "crm.controllers.contract_controller.selectinload",
        side_effect=fake_selectinload,
    ), patch.object(controller.session, "get", return_value=fake_contract), patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):

        with pytest.raises(ValueError):
            controller.get_contract_owner(1)


def test_get_contract_owner_no_permission(controller):
    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.get_contract_owner(1)


# ---------- get_contract_amounts ----------
def test_get_contract_amounts_success(controller):
    fake_contract = MagicMock(amount_total="100", amount_due="50")
    controller.contracts.get_by_id.return_value = fake_contract
    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):
        total, due = controller.get_contract_amounts(1)

    assert total == 100
    assert due == 50


def test_get_contract_amounts_not_found(controller):
    controller.contracts.get_by_id.return_value = None
    with patch(
        "crm.controllers.contract_controller.Permission.read_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.get_contract_amounts(999)


# ---------- create_contract ----------
def test_create_contract_success(controller):
    fake_contract = MagicMock(id=10)
    controller.contracts.create.return_value = fake_contract
    controller.serializer.serialize.return_value = {"id": 10}

    with patch(
        "crm.controllers.contract_controller.Permission.create_permission",
        return_value=True,
    ):
        result = controller.create_contract({"client_id": 1})

    assert result == {"id": 10}


def test_create_contract_no_permission(controller):
    with patch(
        "crm.controllers.contract_controller.Permission.create_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.create_contract({"client_id": 1})


# ---------- update_contract ----------
def test_update_contract_success_admin(controller):
    fake_owner = MagicMock(id=1)
    fake_contract = MagicMock(id=2)
    controller.get_contract_owner = MagicMock(return_value=fake_owner)
    controller.contracts.get_by_id.return_value = fake_contract
    controller.contracts.update.return_value = fake_contract
    controller.serializer.serialize.return_value = {"id": 2}

    with patch(
        "crm.controllers.contract_controller.Permission.update_permission",
        return_value=True,
    ), patch(
        "crm.controllers.contract_controller.Permission.is_admin", return_value=True
    ):
        result = controller.update_contract(2, {"client_id": 5})

    assert result == {"id": 2}


def test_update_contract_non_admin_filters_fields(controller):
    fake_owner = MagicMock(id=1)
    fake_contract = MagicMock(id=2)
    controller.get_contract_owner = MagicMock(return_value=fake_owner)
    controller.contracts.get_by_id.return_value = fake_contract
    controller.contracts.update.return_value = fake_contract
    controller.serializer.serialize.return_value = {"id": 2}

    with patch(
        "crm.controllers.contract_controller.Permission.update_permission",
        return_value=True,
    ), patch(
        "crm.controllers.contract_controller.Permission.is_admin", return_value=False
    ):
        result = controller.update_contract(2, {"client_id": 123, "foo": "bar"})

    assert "client_id" not in controller.contracts.update.call_args[0][1]


def test_update_contract_not_found(controller):
    fake_owner = MagicMock(id=1)
    controller.get_contract_owner = MagicMock(return_value=fake_owner)
    controller.contracts.get_by_id.return_value = None

    with patch(
        "crm.controllers.contract_controller.Permission.update_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.update_contract(2, {"foo": "bar"})


# ---------- delete_contract ----------
def test_delete_contract_success(controller):
    fake_contract = MagicMock(is_signed=False)
    controller.contracts.get_by_id.return_value = fake_contract
    controller.contracts.contract_has_events.return_value = False
    controller.contracts.delete.return_value = True

    with patch(
        "crm.controllers.contract_controller.Permission.delete_permission",
        return_value=True,
    ), patch(
        "crm.controllers.contract_controller.ContractController.is_contract_signed",
        return_value=False,
    ), patch(
        "crm.controllers.contract_controller.Permission.is_admin", return_value=True
    ):
        controller.delete_contract(1)
        controller.contracts.delete.assert_called_once_with(1)


def test_delete_contract_signed_non_admin(controller):
    fake_contract = MagicMock(is_signed=True)
    controller.contracts.get_by_id.return_value = fake_contract
    controller.contracts.contract_has_events.return_value = False

    with patch(
        "crm.controllers.contract_controller.Permission.delete_permission",
        return_value=True,
    ), patch(
        "crm.controllers.contract_controller.ContractController.is_contract_signed",
        return_value=True,
    ), patch(
        "crm.controllers.contract_controller.Permission.is_admin", return_value=False
    ):
        with pytest.raises(PermissionError):
            controller.delete_contract(1)


def test_delete_contract_has_events(controller):
    fake_contract = MagicMock(is_signed=False)
    controller.contracts.get_by_id.return_value = fake_contract
    controller.contracts.contract_has_events.return_value = True

    with patch(
        "crm.controllers.contract_controller.Permission.delete_permission",
        return_value=True,
    ), patch(
        "crm.controllers.contract_controller.Permission.is_admin", return_value=True
    ), patch(
        "crm.controllers.contract_controller.ContractController.is_contract_signed",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.delete_contract(1)


def test_delete_contract_delete_failed(controller):
    fake_contract = MagicMock(is_signed=False)
    controller.contracts.get_by_id.return_value = fake_contract
    controller.contracts.contract_has_events.return_value = False
    controller.contracts.delete.return_value = False

    with patch(
        "crm.controllers.contract_controller.Permission.delete_permission",
        return_value=True,
    ), patch(
        "crm.controllers.contract_controller.Permission.is_admin", return_value=True
    ), patch(
        "crm.controllers.contract_controller.ContractController.is_contract_signed",
        return_value=False,
    ):
        with pytest.raises(ValueError):
            controller.delete_contract(1)
