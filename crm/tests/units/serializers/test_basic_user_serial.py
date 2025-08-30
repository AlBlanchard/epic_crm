import pytest
from unittest.mock import MagicMock, patch
from crm.serializers.user_serializer import UserSerializer


class FakeColumn:
    def __init__(self, name):
        self.name = name


class FakeUser:
    def __init__(self):
        self.__table__ = type("T", (), {})()
        setattr(
            self.__table__,
            "columns",
            [
                FakeColumn("id"),
                FakeColumn("employee_number"),
                FakeColumn("username"),
                FakeColumn("email"),
                FakeColumn("created_at"),
                FakeColumn("updated_at"),
                FakeColumn("password"),
            ],
        )
        self.id = 1
        self.employee_number = 123
        self.username = "jean"
        self.email = "john@example.com"
        self.created_at = FakeDateTime("2023-01-01T00:00:00")
        self.updated_at = FakeDateTime("2023-01-02T00:00:00")
        self.password = "secret"

        # Fake roles
        fake_role = type("R", (), {"name": "admin"})()
        fake_ur = type("UR", (), {"role": fake_role})()
        self.user_roles = [fake_ur]


class FakeDateTime:
    def __init__(self, iso_value):
        self._iso = iso_value

    def isoformat(self):
        return self._iso


# -------- Fixtures --------
@pytest.fixture
def fake_user():
    return FakeUser()


# -------- Tests serialize --------
def test_serialize_basic(fake_user):
    serializer = UserSerializer()
    with patch.object(serializer.valid, "validate_email") as mock_email, patch.object(
        serializer.valid, "validate_int_max_length"
    ) as mock_int, patch.object(
        serializer.valid, "validate_str_max_length"
    ) as mock_str:

        result = serializer.serialize(fake_user)

    assert result["id"] == 1
    assert result["employee_number"] == 123
    assert result["username"] == "jean"
    assert result["email"] == "john@example.com"
    assert result["created_at"] == "2023-01-01T00:00:00"
    assert result["updated_at"] == "2023-01-02T00:00:00"
    assert "password" not in result
    assert result["roles"] == ["admin"]

    mock_email.assert_called_once_with("john@example.com")
    mock_int.assert_called_once_with(123)
    mock_str.assert_called_once_with("jean")


def test_serialize_fields_subset(fake_user):
    serializer = UserSerializer(fields=["id", "username"], include_roles=False)
    result = serializer.serialize(fake_user)
    assert set(result.keys()) == {"id", "username"}
    assert "roles" not in result


def test_serialize_without_roles(fake_user):
    serializer = UserSerializer(include_roles=False)
    result = serializer.serialize(fake_user)
    assert "roles" not in result


def test_serialize_with_extra(fake_user):
    serializer = UserSerializer()
    result = serializer.serialize(fake_user, extra={"extra_key": "extra_value"})
    assert result["extra_key"] == "extra_value"


def test_serialize_none_user():
    serializer = UserSerializer()
    assert serializer.serialize(None) == {}  # type: ignore


# -------- Tests serialize_list --------
def test_serialize_list(fake_user):
    serializer = UserSerializer()
    result = serializer.serialize_list([fake_user, None])  # type: ignore
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == 1
