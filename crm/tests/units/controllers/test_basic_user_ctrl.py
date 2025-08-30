import pytest
from unittest.mock import MagicMock, patch
from crm.controllers.user_controller import UserController


@pytest.fixture
def controller():
    ctrl = UserController(session=MagicMock())
    ctrl._get_current_user = MagicMock(return_value=MagicMock(id=1, username="me"))
    ctrl._setup_services()
    # Mock des services
    ctrl.users = MagicMock()
    ctrl.roles = MagicMock()
    ctrl.serializer = MagicMock()
    return ctrl


# ---------- get_user ----------
def test_get_user_success(controller):
    fake_user = MagicMock(id=2, username="alex")
    controller.users.get_by_id.return_value = fake_user
    controller.serializer.serialize.return_value = {"id": 2, "username": "alex"}

    with patch(
        "crm.controllers.user_controller.Permission.read_permission", return_value=True
    ):
        result = controller.get_user(2)

    assert result == {"id": 2, "username": "alex"}
    controller.users.get_by_id.assert_called_once_with(2)


def test_get_user_no_permission(controller):
    controller.users.get_by_id.return_value = MagicMock(id=2)
    with patch(
        "crm.controllers.user_controller.Permission.read_permission", return_value=False
    ):
        with pytest.raises(PermissionError):
            controller.get_user(2)


def test_get_user_not_found(controller):
    controller.users.get_by_id.return_value = None
    with patch(
        "crm.controllers.user_controller.Permission.read_permission", return_value=True
    ):
        with pytest.raises(ValueError):
            controller.get_user(999)


# ---------- get_all_users ----------
def test_get_all_users_success(controller):
    fake_user = MagicMock(id=1, username="alex")
    controller.users.get_all.return_value = [fake_user]
    controller.serializer.serialize_list.return_value = [{"id": 1, "username": "alex"}]

    with patch(
        "crm.controllers.user_controller.Permission.read_permission", return_value=True
    ):
        result = controller.get_all_users()

    assert result == [{"id": 1, "username": "alex"}]
    controller.users.get_all.assert_called_once()


def test_get_all_users_no_permission(controller):
    with patch(
        "crm.controllers.user_controller.Permission.read_permission", return_value=False
    ):
        with pytest.raises(PermissionError):
            controller.get_all_users()


# ---------- create_user ----------
def test_create_user_success(controller):
    data = {
        "username": "alex",
        "email": "alex@test.com",
        "employee_number": 123,
        "password": "pass",
    }

    controller.get_all_employees_nbr = MagicMock(return_value=[111, 222])
    controller.valid = MagicMock()
    controller.users.create_user.return_value = MagicMock(id=3, username="alex")
    controller.serializer.serialize.return_value = {"id": 3, "username": "alex"}

    with patch(
        "crm.controllers.user_controller.Permission.create_permission",
        return_value=True,
    ):
        result = controller.create_user(data)

    assert result == {"id": 3, "username": "alex"}
    controller.valid.validate_employee_number.assert_called_once()


def test_create_user_no_permission(controller):
    data = {
        "username": "alex",
        "email": "alex@test.com",
        "employee_number": 123,
        "password": "pass",
    }
    with patch(
        "crm.controllers.user_controller.Permission.create_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.create_user(data)


# ---------- update_user ----------
def test_update_user_success(controller):
    fake_user = MagicMock(id=2)
    controller.users.get_by_id.return_value = fake_user
    controller.users.update_user.return_value = fake_user
    controller.serializer.serialize.return_value = {"id": 2}

    with patch(
        "crm.controllers.user_controller.Permission.update_permission",
        return_value=True,
    ), patch("crm.controllers.user_controller.Permission.is_admin", return_value=False):
        result = controller.update_user(2, {"username": "newname"})

    assert result == {"id": 2}


def test_update_user_not_found(controller):
    controller.users.get_by_id.return_value = None
    with patch(
        "crm.controllers.user_controller.Permission.update_permission",
        return_value=True,
    ):
        with pytest.raises(ValueError):
            controller.update_user(2, {"username": "newname"})


def test_update_user_no_permission(controller):
    controller.users.get_by_id.return_value = MagicMock(id=2)
    with patch(
        "crm.controllers.user_controller.Permission.update_permission",
        return_value=False,
    ):
        with pytest.raises(PermissionError):
            controller.update_user(2, {"username": "newname"})
