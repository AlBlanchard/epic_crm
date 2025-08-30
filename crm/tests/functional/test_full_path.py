import pytest
from crm.models.user import User
from crm.models.role import Role


def test_create_user_with_role(db_session):
    role = Role(name="admin")
    user = User(
        employee_number=1,
        username="alex",
        email="alex@test.com",
        password_hash="fakehash",
    )
    user.add_role(role, db_session)

    db_session.add(role)
    db_session.add(user)
    db_session.commit()

    assert role in user.roles
    assert user.has_role(role) is True
