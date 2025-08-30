import pytest
from unittest.mock import MagicMock, patch
from crm.controllers.main_controller import MainController


@pytest.fixture
def controller():
    ctrl = MainController(session=MagicMock())
    ctrl._setup_services()
    ctrl.view = MagicMock()
    ctrl.user_menu_ctrl = MagicMock()
    ctrl.client_menu_ctrl = MagicMock()
    ctrl.contract_menu_ctrl = MagicMock()
    ctrl.event_menu_ctrl = MagicMock()
    ctrl.user_ctrl = MagicMock()
    ctrl.auth_ctrl = MagicMock()
    return ctrl


# ---------- _filter_items_by_permissions ----------
def test_filter_items_by_permissions(controller):
    user = MagicMock()
    raw_items = [("item1", lambda: "ok", ["READ"], "user")]
    with patch(
        "crm.controllers.main_controller.Permission.has_permission", return_value=True
    ):
        allowed = controller._filter_items_by_permissions(user, raw_items)
    assert allowed == [("item1", raw_items[0][1])]


def test_filter_items_by_permissions_none(controller):
    user = MagicMock()
    raw_items = [("item1", lambda: "ok", ["READ"], "user")]
    with patch(
        "crm.controllers.main_controller.Permission.has_permission", return_value=False
    ):
        allowed = controller._filter_items_by_permissions(user, raw_items)
    assert allowed == []


# ---------- _run_generic_menu ----------
def test_run_generic_menu_exit(monkeypatch, controller):
    controller.view.run_menu.return_value = "0"
    controller.user_menu_ctrl._get_current_user.return_value = MagicMock()

    with pytest.raises(SystemExit):
        controller._run_generic_menu(
            "title", [("label", lambda: None, ["READ"], "user")]
        )


def test_run_generic_menu_logout(controller):
    controller.view.run_menu.side_effect = ["R"]  # simule le logout
    controller.user_menu_ctrl._get_current_user.return_value = MagicMock()
    controller.auth_ctrl.logout = MagicMock()

    controller._run_generic_menu(
        "title", [("label", lambda: None, ["READ"], "user")], logout=True
    )

    controller.auth_ctrl.logout.assert_called_once()


def test_run_generic_menu_valid_choice(controller):
    action = MagicMock()
    raw_items = [("label", action, ["READ"], "user")]

    controller.user_menu_ctrl._get_current_user.return_value = MagicMock()
    controller.view.run_menu.side_effect = [1, "R"]  # Choisi l'item puis exit la loop

    with patch(
        "crm.controllers.main_controller.Permission.has_permission", return_value=True
    ):
        controller._run_generic_menu("title", raw_items)

    action.assert_called_once()


def test_run_generic_menu_invalid_choice(controller):
    action = MagicMock()
    raw_items = [("label", action, ["READ"], "user")]

    controller.user_menu_ctrl._get_current_user.return_value = MagicMock()
    controller.view.run_menu.side_effect = [99, "R"]  # Invalid index puis exit la loop

    with patch(
        "crm.controllers.main_controller.Permission.has_permission", return_value=True
    ):
        controller._run_generic_menu("title", raw_items)

    action.assert_not_called()


# ---------- run ----------
def test_run_auth_required(controller):
    controller.auth_ctrl.me_safe.return_value = False
    controller.auth_ctrl.login_interactive = MagicMock()
    controller.show_main_menu = MagicMock()

    controller.run()

    controller.auth_ctrl.login_interactive.assert_called_once()
    controller.show_main_menu.assert_called_once()


def test_run_already_authenticated(controller):
    controller.auth_ctrl.me_safe.return_value = True
    controller.show_main_menu = MagicMock()

    controller.run()

    controller.show_main_menu.assert_called_once()


# ---------- show_menu ----------
def test_show_main_menu(controller):
    controller._run_generic_menu = MagicMock()
    controller.show_main_menu()
    controller._run_generic_menu.assert_called_once()
    args, kwargs = controller._run_generic_menu.call_args
    assert kwargs["logout"] is True  # menu principal doit logout


def test_show_menu_clients(controller):
    controller._run_generic_menu = MagicMock()
    controller.show_menu_clients()
    controller._run_generic_menu.assert_called_once()


def test_show_menu_contracts(controller):
    controller._run_generic_menu = MagicMock()
    controller.show_menu_contracts()
    controller._run_generic_menu.assert_called_once()


def test_show_menu_events(controller):
    controller._run_generic_menu = MagicMock()
    controller.show_menu_events()
    controller._run_generic_menu.assert_called_once()


def test_show_menu_users(controller):
    controller._run_generic_menu = MagicMock()
    controller.show_menu_users()
    controller._run_generic_menu.assert_called_once()


def test_show_menu_modify_user(controller):
    controller._run_generic_menu = MagicMock()
    controller.user_ctrl.get_user_name.return_value = "TestUser"
    controller.show_menu_modify_user(1)
    controller._run_generic_menu.assert_called_once()
    args, kwargs = controller._run_generic_menu.call_args
    assert "TestUser" in args[0]  # titre du menu doit inclure le nom de l'utilisateur
