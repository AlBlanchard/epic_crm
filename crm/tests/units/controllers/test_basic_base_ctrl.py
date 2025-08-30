import pytest
from unittest.mock import MagicMock, patch
from crm.controllers.base import AbstractController


# Petite classe dummy pour tester AbstractController
class DummyController(AbstractController):
    def _setup_services(self):
        self.extra = "ok"


@pytest.fixture
def controller():
    return DummyController(session=MagicMock())


# ---------- _get_current_user ----------
@pytest.mark.no_bypass_auth
def test_get_current_user_no_token(controller):
    with patch("crm.controllers.base.Authentication.load_token", return_value=None):
        with pytest.raises(PermissionError):
            controller._get_current_user()


@pytest.mark.no_bypass_auth
def test_get_current_user_user_not_found(controller):
    with patch(
        "crm.controllers.base.Authentication.load_token", return_value="tok"
    ), patch(
        "crm.controllers.base.Authentication.verify_token", return_value={"sub": "1"}
    ), patch.object(
        controller.user_crud, "get_by_id", return_value=None
    ):
        with pytest.raises(PermissionError):
            controller._get_current_user()


@pytest.mark.no_bypass_auth
def test_get_current_user_success(controller):
    fake_user = MagicMock(id=1)
    with patch(
        "crm.controllers.base.Authentication.load_token", return_value="tok"
    ), patch(
        "crm.controllers.base.Authentication.verify_token", return_value={"sub": "1"}
    ), patch.object(
        controller.user_crud, "get_by_id", return_value=fake_user
    ):
        me = controller._get_current_user()
    assert me == fake_user


# ---------- _ensure_admin ----------
@pytest.mark.no_bypass_auth
def test_ensure_admin_success(controller):
    fake_user = MagicMock()
    with patch("crm.controllers.base.Permission.is_admin", return_value=True):
        controller._ensure_admin(fake_user)  # pas d'exception


@pytest.mark.no_bypass_auth
def test_ensure_admin_forbidden(controller):
    fake_user = MagicMock()
    with patch("crm.controllers.base.Permission.is_admin", return_value=False):
        with pytest.raises(PermissionError):
            controller._ensure_admin(fake_user)


# ---------- _ensure_owner_or_admin ----------
@pytest.mark.no_bypass_auth
def test_ensure_owner_or_admin_as_admin(controller):
    fake_user = MagicMock(id=2)
    with patch("crm.controllers.base.Permission.is_admin", return_value=True):
        controller._ensure_owner_or_admin(fake_user, owner_id=1)  # pas d'exception


@pytest.mark.no_bypass_auth
def test_ensure_owner_or_admin_as_owner(controller):
    fake_user = MagicMock(id=1)
    with patch("crm.controllers.base.Permission.is_admin", return_value=False):
        controller._ensure_owner_or_admin(fake_user, owner_id=1)  # pas d'exception


@pytest.mark.no_bypass_auth
def test_ensure_owner_or_admin_forbidden(controller):
    fake_user = MagicMock(id=2)
    with patch("crm.controllers.base.Permission.is_admin", return_value=False):
        with pytest.raises(PermissionError):
            controller._ensure_owner_or_admin(fake_user, owner_id=1)
