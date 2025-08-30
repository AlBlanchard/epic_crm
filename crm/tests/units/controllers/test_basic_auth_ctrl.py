import pytest
from unittest.mock import MagicMock, patch
from crm.controllers.auth_controller import AuthController


@pytest.fixture
def controller():
    ctrl = AuthController(session=MagicMock())
    ctrl._setup_services()
    ctrl.users = MagicMock()
    ctrl.serializer = MagicMock()
    ctrl.jti_store = MagicMock()
    return ctrl


# ---------- login ----------
def test_login_success(controller):
    fake_tokens = {"access_token": "acc123", "refresh_token": "ref123"}
    fake_payload_access = {"sub": "1", "jti": "jti1"}
    fake_payload_refresh = {"sub": "1", "jti": "jti2"}
    fake_user = MagicMock(id=1)

    with patch(
        "crm.controllers.auth_controller.Authentication.authenticate_user",
        return_value=fake_tokens,
    ), patch(
        "crm.controllers.auth_controller.Authentication.verify_token_without_jti",
        side_effect=[fake_payload_access, fake_payload_refresh],
    ), patch(
        "crm.controllers.auth_controller.Authentication.save_token"
    ):

        controller.users.get_by_id.return_value = fake_user
        controller.serializer.serialize.return_value = {"id": 1, "username": "alex"}

        result = controller.login("alex", "pass")

    assert result["message"] == "Authentification réussie."
    assert "access_token" in result
    controller.jti_store.add.assert_any_call("jti1")
    controller.jti_store.add.assert_any_call("jti2")


def test_login_user_not_found(controller):
    fake_tokens = {"access_token": "acc123", "refresh_token": "ref123"}
    fake_payload = {"sub": "999", "jti": "jti"}
    with patch(
        "crm.controllers.auth_controller.Authentication.authenticate_user",
        return_value=fake_tokens,
    ), patch(
        "crm.controllers.auth_controller.Authentication.verify_token_without_jti",
        return_value=fake_payload,
    ), patch(
        "crm.controllers.auth_controller.Authentication.save_token"
    ):

        controller.users.get_by_id.return_value = None

        with pytest.raises(ValueError):
            controller.login("alex", "pass")


# ---------- me ----------
def test_me_success(controller):
    fake_payload = {"sub": "1"}
    fake_user = MagicMock(id=1)
    controller.users.get_by_id.return_value = fake_user
    controller.serializer.serialize.return_value = {"id": 1, "username": "alex"}

    with patch(
        "crm.controllers.auth_controller.Authentication.load_token",
        return_value="token123",
    ), patch(
        "crm.controllers.auth_controller.Authentication.verify_token",
        return_value=fake_payload,
    ):

        result = controller.me()

    assert result == {"id": 1, "username": "alex"}


def test_me_no_token(controller):
    with patch(
        "crm.controllers.auth_controller.Authentication.load_token", return_value=None
    ):
        with pytest.raises(PermissionError):
            controller.me()


def test_me_user_not_found(controller):
    fake_payload = {"sub": "1"}
    controller.users.get_by_id.return_value = None

    with patch(
        "crm.controllers.auth_controller.Authentication.load_token",
        return_value="token123",
    ), patch(
        "crm.controllers.auth_controller.Authentication.verify_token",
        return_value=fake_payload,
    ):

        with pytest.raises(ValueError):
            controller.me()


# ---------- me_safe ----------
def test_me_safe_success(controller):
    with patch.object(controller, "me", return_value={"id": 1}):
        assert controller.me_safe() == {"id": 1}


def test_me_safe_exception(controller):
    with patch.object(controller, "me", side_effect=Exception("fail")):
        assert controller.me_safe() is None


# ---------- refresh ----------
def test_refresh_success(controller):
    with patch(
        "crm.controllers.auth_controller.Authentication.refresh_access_token",
        return_value="new_token",
    ):
        result = controller.refresh("refresh123")
    assert result == {"message": "Access token rafraîchi.", "access_token": "new_token"}


# ---------- logout ----------
def test_logout_success(controller, tmp_path):
    fake_access_payload = {"sub": "1", "jti": "jti1"}
    fake_refresh_payload = {"sub": "1", "jti": "jti2"}
    token_path = tmp_path / "tokenfile"

    with patch(
        "crm.controllers.auth_controller.Authentication.load_token", return_value="acc"
    ), patch(
        "crm.controllers.auth_controller.Authentication.verify_token_without_jti",
        side_effect=[fake_access_payload, fake_refresh_payload],
    ), patch(
        "crm.auth.config.TOKEN_PATH", token_path
    ):

        result = controller.logout(refresh_token="ref")

    assert result == {"message": "Déconnexion réussie."}
    controller.jti_store.revoke.assert_any_call("jti1")
    controller.jti_store.revoke.assert_any_call("jti2")
