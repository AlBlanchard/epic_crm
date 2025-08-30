import pytest
from unittest.mock import MagicMock, patch
from crm.controllers.client_controller import ClientController


@pytest.fixture
def controller():
    ctrl = ClientController(session=MagicMock())
    ctrl._setup_services()
    ctrl.clients = MagicMock()
    ctrl.users = MagicMock()
    ctrl.serializer = MagicMock()
    ctrl._get_current_user = MagicMock(return_value=MagicMock(id=1))
    return ctrl


# ---------- list_all ----------
def test_list_all_success(controller):
    fake_client = MagicMock(id=1)
    controller.clients.get_all.return_value = [fake_client]
    controller.serializer.serialize_list.return_value = [{"id": 1}]

    with patch(
        "crm.controllers.client_controller.Permission.read_permission",
        return_value=True,
    ):
        result = controller.list_all()

    assert result == [{"id": 1}]
    controller.clients.get_all.assert_called_once()


def test_list_all_no_permission(controller):
    with patch(
        "crm.controllers.client_controller.Permission.read_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.list_all()


# ---------- get_client ----------
def test_get_client_success(controller):
    fake_client = MagicMock(id=2, sales_contact_id=1)
    controller.clients.get_by_id.return_value = fake_client
    controller.serializer.serialize.return_value = {"id": 2}

    with patch(
        "crm.controllers.client_controller.Permission.read_permission",
        return_value=True,
    ), patch.object(controller, "_ensure_owner_or_admin", return_value=True):
        result = controller.get_client(2)

    assert result == {"id": 2}


def test_get_client_not_found(controller):
    controller.clients.get_by_id.return_value = None
    with patch(
        "crm.controllers.client_controller.Permission.read_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.get_client(999)


def test_get_client_no_permission(controller):
    with patch(
        "crm.controllers.client_controller.Permission.read_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.get_client(1)


# ---------- get_owner ----------
def test_get_owner_success(controller):
    fake_client = MagicMock(id=2, sales_contact_id=99)
    fake_user = MagicMock(id=99)
    controller.clients.get_by_id.return_value = fake_client
    controller.users.get_by_id.return_value = fake_user

    with patch(
        "crm.controllers.client_controller.Permission.read_permission",
        return_value=True,
    ):
        result = controller.get_owner(2)

    assert result == fake_user


def test_get_owner_not_found(controller):
    controller.clients.get_by_id.return_value = None
    with patch(
        "crm.controllers.client_controller.Permission.read_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.get_owner(999)


# ---------- create_client ----------
def test_create_client_success(controller):
    fake_client = MagicMock(id=10)
    controller.clients.create_client.return_value = fake_client
    controller.serializer.serialize.return_value = {"id": 10}

    with patch(
        "crm.controllers.client_controller.Permission.create_permission",
        return_value=True,
    ), patch(
        "crm.controllers.client_controller.Permission.is_admin", return_value=True
    ):
        result = controller.create_client(
            {"name": "Test Client", "sales_contact_id": 5}
        )

    assert result == {"id": 10}
    controller.clients.create_client.assert_called_once()


def test_create_client_sales_assigning_other(controller):
    with patch(
        "crm.controllers.client_controller.Permission.create_permission",
        return_value=True,
    ), patch(
        "crm.controllers.client_controller.Permission.is_admin", return_value=False
    ):
        with pytest.raises(PermissionError):
            controller.create_client({"sales_contact_id": 99})


def test_create_client_no_permission(controller):
    with patch(
        "crm.controllers.client_controller.Permission.create_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.create_client({"name": "Test"})


# ---------- update_client ----------
def test_update_client_success(controller):
    fake_client = MagicMock(id=2, sales_contact_id=1)
    controller.clients.get_by_id.return_value = fake_client
    controller.clients.update_client.return_value = fake_client
    controller.serializer.serialize.return_value = {"id": 2}

    with patch.object(controller, "_ensure_owner_or_admin", return_value=True), patch(
        "crm.controllers.client_controller.Permission.is_admin", return_value=True
    ):
        result = controller.update_client(2, {"name": "New Name"})

    assert result == {"id": 2}


def test_update_client_not_found(controller):
    controller.clients.get_by_id.return_value = None
    with pytest.raises(ValueError):
        controller.update_client(2, {"name": "New"})


def test_update_client_reassign_non_admin(controller):
    fake_client = MagicMock(id=2, sales_contact_id=1)
    controller.clients.get_by_id.return_value = fake_client

    with patch.object(controller, "_ensure_owner_or_admin", return_value=True), patch(
        "crm.controllers.client_controller.Permission.is_admin", return_value=False
    ):
        with pytest.raises(PermissionError):
            controller.update_client(2, {"sales_contact_id": 99})


# ---------- delete_client ----------
def test_delete_client_success(controller):
    fake_client = MagicMock(id=2)
    controller.clients.get_by_id.return_value = fake_client
    controller.clients.client_has_contracts.return_value = False
    controller.clients.delete_client.return_value = True

    with patch(
        "crm.controllers.client_controller.Permission.delete_permission",
        return_value=True,
    ):
        controller.delete_client(2)
        controller.clients.delete_client.assert_called_once_with(2)


def test_delete_client_with_contracts(controller):
    fake_client = MagicMock(id=2)
    controller.clients.get_by_id.return_value = fake_client
    controller.clients.client_has_contracts.return_value = True

    with patch(
        "crm.controllers.client_controller.Permission.delete_permission",
        return_value=True,
    ):
        with pytest.raises(PermissionError):
            controller.delete_client(2)


def test_delete_client_not_found(controller):
    controller.clients.get_by_id.return_value = None
    with patch(
        "crm.controllers.client_controller.Permission.delete_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.delete_client(999)


# ---------- assign_sales_contact ----------
def test_assign_sales_contact_success(controller):
    fake_client = MagicMock(id=2)
    controller.clients.assign_sales_contact.return_value = True
    controller.clients.get_by_id.return_value = fake_client
    controller.serializer.serialize.return_value = {"id": 2}

    with patch.object(controller, "_ensure_admin", return_value=True):
        result = controller.assign_sales_contact(2, 99)

    assert result == {"id": 2}


def test_assign_sales_contact_fail(controller):
    controller.clients.assign_sales_contact.return_value = False
    with patch.object(controller, "_ensure_admin", return_value=True):
        with pytest.raises(ValueError):
            controller.assign_sales_contact(2, 99)
