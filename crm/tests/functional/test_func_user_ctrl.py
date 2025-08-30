import pytest
from crm.controllers.user_controller import UserController
from crm.models.user import User
from crm.models.role import Role


@pytest.fixture
def user_ctrl(db_session, monkeypatch):
    ctrl = UserController(session=db_session)

    admin = User(
        employee_number=1,
        username="admin",
        email="admin@test.com",
        password_hash="hash",
    )
    role_admin = Role(name="admin")
    db_session.add_all([admin, role_admin])
    db_session.commit()

    # Associe l'utilisateur au rôle admin
    admin.add_role(role_admin, db_session)
    db_session.commit()

    monkeypatch.setattr(ctrl, "_get_current_user", lambda: admin)
    return ctrl, admin


# ---------- CREATE ----------


def test_create_user_success(user_ctrl, db_session):
    ctrl, admin = user_ctrl
    data = {
        "username": "tealc",
        "email": "tealc@test.com",
        "employee_number": 2,
        "password": "pwd123",
    }
    result = ctrl.create_user(data)

    assert result["username"] == "tealc"
    created = db_session.query(User).filter_by(username="tealc").first()
    assert created is not None
    assert created.email == "tealc@test.com"


def test_create_user_duplicate_email(user_ctrl):
    ctrl, admin = user_ctrl
    data = {
        "username": "tealc",
        "email": "admin@test.com",  # déjà pris
        "employee_number": 3,
        "password": "pwd123",
    }
    with pytest.raises(ValueError):
        ctrl.create_user(data)


# ---------- READ ----------


def test_get_user_success(user_ctrl, db_session):
    ctrl, admin = user_ctrl
    user = User(
        employee_number=10,
        username="alice",
        email="alice@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    db_session.commit()

    result = ctrl.get_user(user.id)
    assert result["username"] == "alice"


def test_get_user_not_found(user_ctrl):
    ctrl, admin = user_ctrl
    with pytest.raises(ValueError):
        ctrl.get_user(999)


# ---------- UPDATE ----------


def test_update_user_success(user_ctrl, db_session):
    ctrl, admin = user_ctrl
    user = User(
        employee_number=20,
        username="eva",
        email="eva@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    db_session.commit()

    result = ctrl.update_user(user.id, {"username": "eva-updated"})
    assert result["username"] == "eva-updated"


def test_update_user_not_found(user_ctrl):
    ctrl, admin = user_ctrl
    with pytest.raises(ValueError):
        ctrl.update_user(999, {"username": "ghost"})


# ---------- DELETE ----------


def test_delete_user_success(user_ctrl, db_session):
    ctrl, admin = user_ctrl
    user = User(
        employee_number=30,
        username="franck",
        email="franck@test.com",
        password_hash="hash",
    )
    db_session.add(user)
    db_session.commit()

    ctrl.delete_user(user.id)

    assert db_session.query(User).filter_by(id=user.id).first() is None


def test_delete_user_not_found(user_ctrl):
    ctrl, admin = user_ctrl
    with pytest.raises(ValueError):
        ctrl.delete_user(999)


# ---------- ROLES ----------


def test_add_role_success(user_ctrl, db_session):
    ctrl, admin = user_ctrl
    user = User(
        employee_number=40,
        username="sam",
        email="sam@test.com",
        password_hash="hash",
    )
    role = Role(name="sales")
    db_session.add_all([user, role])
    db_session.commit()

    ctrl.add_role(user.id, role.id)

    roles = ctrl.get_user_roles(user.id)
    assert "sales" in roles


def test_add_role_already_assigned(user_ctrl, db_session):
    ctrl, admin = user_ctrl
    user = User(
        employee_number=41,
        username="tom",
        email="tom@test.com",
        password_hash="hash",
    )
    role = Role(name="support")
    db_session.add_all([user, role])
    db_session.commit()

    ctrl.add_role(user.id, role.id)
    with pytest.raises(ValueError):
        ctrl.add_role(user.id, role.id)


def test_remove_role_success(user_ctrl, db_session):
    ctrl, admin = user_ctrl
    user = User(
        employee_number=42,
        username="lea",
        email="lea@test.com",
        password_hash="hash",
    )
    role = Role(name="management")
    db_session.add_all([user, role])
    db_session.commit()

    ctrl.add_role(user.id, role.id)
    ctrl.remove_role(user.id, role.id)

    roles = ctrl.get_user_roles(user.id)
    assert "management" not in roles


def test_remove_role_not_found(user_ctrl, db_session):
    ctrl, admin = user_ctrl
    user = User(
        employee_number=43,
        username="norbert",
        email="norbert@test.com",
        password_hash="hash",
    )
    role = Role(name="ghost")
    db_session.add_all([user, role])
    db_session.commit()

    with pytest.raises(ValueError):
        ctrl.remove_role(user.id, role.id)
