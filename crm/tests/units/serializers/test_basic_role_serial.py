import pytest
from crm.serializers.role_serializer import RoleSerializer


class FakeColumn:
    def __init__(self, name):
        self.name = name


class FakeDateTime:
    def __init__(self, iso_value):
        self._iso = iso_value

    def isoformat(self):
        return self._iso


class FakeRole:
    def __init__(self):
        self.__table__ = type("T", (), {})()
        setattr(
            self.__table__,
            "columns",
            [
                FakeColumn("id"),
                FakeColumn("name"),
                FakeColumn("created_at"),
                FakeColumn("updated_at"),
            ],
        )
        self.id = 1
        self.name = "admin"
        self.created_at = FakeDateTime("2023-01-01T00:00:00")
        self.updated_at = FakeDateTime("2023-01-02T00:00:00")

    @pytest.fixture
    def fake_role():
        return FakeRole()

    def test_serialize_basic(fake_role):  # type: ignore
        serializer = RoleSerializer()
        result = serializer.serialize(fake_role)  # type: ignore

        # Vérifie que les champs publics sont présents
        for field in RoleSerializer.PUBLIC_FIELDS:
            assert field in result

        assert result["id"] == 1
        assert result["name"] == "admin"
        assert result["created_at"] == "2023-01-01T00:00:00"
        assert result["updated_at"] == "2023-01-02T00:00:00"

    def test_serialize_with_extra(fake_role):  # type: ignore
        serializer = RoleSerializer()
        result = serializer.serialize(fake_role, extra={"extra": "value"})  # type: ignore
        assert result["extra"] == "value"

    def test_serialize_none_role():  # type: ignore
        serializer = RoleSerializer()
        assert serializer.serialize(None) == {}  # type: ignore

    def test_serialize_list(fake_role):  # type: ignore
        serializer = RoleSerializer()
        result = serializer.serialize_list([fake_role, None])  # type: ignore
        assert isinstance(result, list)
        assert result[0]["id"] == 1
