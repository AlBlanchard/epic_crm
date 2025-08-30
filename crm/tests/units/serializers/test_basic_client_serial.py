import pytest
from unittest.mock import patch
from crm.serializers.client_serializer import ClientSerializer


class FakeColumn:
    def __init__(self, name):
        self.name = name


class FakeDateTime:
    def __init__(self, iso_value):
        self._iso = iso_value

    def isoformat(self):
        return self._iso


class FakeSalesContact:
    sales_contact_name = "Jean Dubosquet"


class FakeClient:
    def __init__(self, with_contact=True):
        self.__table__ = type("T", (), {})()
        setattr(
            self.__table__,
            "columns",
            [
                FakeColumn("id"),
                FakeColumn("full_name"),
                FakeColumn("email"),
                FakeColumn("phone"),
                FakeColumn("company_name"),
                FakeColumn("sales_contact_id"),
                FakeColumn("created_at"),
                FakeColumn("updated_at"),
            ],
        )
        self.id = 1
        self.full_name = "Client Test"
        self.email = "client@example.com"
        self.phone = "0102030405"
        self.company_name = "ACME Inc."
        self.sales_contact_id = 42
        self.created_at = FakeDateTime("2023-01-01T00:00:00")
        self.updated_at = FakeDateTime("2023-01-02T00:00:00")

        if with_contact:
            self.sales_contact = FakeSalesContact()
            self.sales_contact_name = "Jean Dubosquet"
        else:
            self.sales_contact = None
            self.sales_contact_name = None


@pytest.fixture
def fake_client():
    return FakeClient(with_contact=True)


def test_serialize_basic(fake_client):
    serializer = ClientSerializer()
    with patch.object(serializer.valid, "validate_email") as mock_email, patch.object(
        serializer.valid, "validate_phone"
    ) as mock_phone, patch.object(
        serializer.valid, "validate_str_max_length"
    ) as mock_str:

        result = serializer.serialize(fake_client)

    # Vérifie que toutes les clés publiques sont présentes
    for field in ClientSerializer.PUBLIC_FIELDS:
        assert field in result

    # Vérifie le champ calculé
    assert result["sales_contact_name"] == "Jean Dubosquet"

    # Vérifie que les validateurs ont été appelés
    mock_email.assert_called_once_with("client@example.com")
    mock_phone.assert_called_once_with("0102030405")
    assert mock_str.call_count >= 2


def test_serialize_no_contact():
    client = FakeClient(with_contact=False)
    serializer = ClientSerializer()
    result = serializer.serialize(client)  # type: ignore
    assert (
        result["sales_contact_name"] == "Aucun contact"
        or result["sales_contact_name"] == "Aucun"
    )


def test_serialize_with_extra(fake_client):
    serializer = ClientSerializer()
    result = serializer.serialize(fake_client, extra={"extra": "value"})
    assert result["extra"] == "value"


def test_serialize_none_client():
    serializer = ClientSerializer()
    assert serializer.serialize(None) == {}  # type: ignore


def test_serialize_list(fake_client):
    serializer = ClientSerializer()
    result = serializer.serialize_list([fake_client, None])  # type: ignore
    assert isinstance(result, list)
    assert len(result) == 2  # None est sérialisé en {}
    assert result[0]["id"] == 1
