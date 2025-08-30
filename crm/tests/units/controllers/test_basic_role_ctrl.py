import pytest
from unittest.mock import MagicMock, patch
from crm.controllers.role_controller import RoleController


@pytest.fixture
def controller():
    ctrl = RoleController(session=MagicMock())
    ctrl._setup_services()
    ctrl.roles = MagicMock()
    ctrl.users = MagicMock()
    ctrl.role_serializer = MagicMock()
    ctrl.user_serializer = MagicMock()
    ctrl._get_current_user = MagicMock(return_value=MagicMock(id=1))
    return ctrl


# ---------- list_roles ----------
def test_list_roles_admin(controller):
    fake_roles = [MagicMock(name="admin"), MagicMock(name="sales")]
    controller.roles.get_all.return_value = fake_roles
    controller.role_serializer.serialize_list.return_value = [
        {"name": "admin"},
        {"name": "sales"},
    ]

    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=True):
        result = controller.list_roles()

    assert {"name": "admin"} in result
    assert {"name": "sales"} in result


def test_list_roles_non_admin(controller):
    fake_roles = [MagicMock(name="admin"), MagicMock(name="sales")]
    controller.roles.get_all.return_value = fake_roles
    controller.role_serializer.serialize_list.return_value = [{"name": "sales"}]

    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=False):
        result = controller.list_roles()

    assert {"name": "sales"} in result
    assert all(r["name"] != "admin" for r in result)


def test_list_roles_no_permission(controller):
    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=False
    ):
        with pytest.raises(ValueError):
            controller.list_roles()


# ---------- get_role ----------
def test_get_role_admin_success(controller):
    fake_role = MagicMock(name="admin")
    controller.roles.get_by_id.return_value = fake_role
    controller.role_serializer.serialize.return_value = {"name": "admin"}

    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=True):
        result = controller.get_role(1)

    assert result == {"name": "admin"}


def test_get_role_non_admin_success(controller):
    fake_role = MagicMock(name="sales")
    controller.roles.get_by_id.return_value = fake_role
    controller.role_serializer.serialize.return_value = {"name": "sales"}

    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=False):
        result = controller.get_role(2)

    assert result == {"name": "sales"}


def test_get_role_non_admin_forbidden_admin_role(controller):
    fake_role = MagicMock()
    fake_role.name = "admin"  # plus sûr que MagicMock(name="admin") qui définit juste le nom interne du mock et pas la value.
    controller.roles.get_by_id.return_value = fake_role

    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=False):
        with pytest.raises(ValueError):
            controller.get_role(1)


def test_get_role_not_found(controller):
    controller.roles.get_by_id.return_value = None
    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=True):
        with pytest.raises(ValueError):
            controller.get_role(999)


# ---------- get_role_by_name ----------
def test_get_role_by_name_admin_success(controller):
    fake_role = MagicMock(name="admin")
    controller.roles.find_by_name.return_value = fake_role
    controller.role_serializer.serialize.return_value = {"name": "admin"}

    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=True):
        result = controller.get_role_by_name("admin")

    assert result == {"name": "admin"}


def test_get_role_by_name_non_admin_success(controller):
    fake_role = MagicMock(name="sales")
    controller.roles.find_by_name.return_value = fake_role
    controller.role_serializer.serialize.return_value = {"name": "sales"}

    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=False):
        result = controller.get_role_by_name("sales")

    assert result == {"name": "sales"}


def test_get_role_by_name_non_admin_forbidden(controller):
    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=False):
        with pytest.raises(ValueError):
            controller.get_role_by_name("admin")


def test_get_role_by_name_not_found(controller):
    controller.roles.find_by_name.return_value = None
    with patch(
        "crm.controllers.role_controller.Permission.read_permission", return_value=True
    ), patch("crm.controllers.role_controller.Permission.is_admin", return_value=True):
        with pytest.raises(ValueError):
            controller.get_role_by_name("ghost")
