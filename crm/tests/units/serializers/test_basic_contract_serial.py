import pytest
from unittest.mock import patch
from crm.serializers.contract_serializer import ContractSerializer


class FakeColumn:
    def __init__(self, name):
        self.name = name


class FakeDateTime:
    def __init__(self, iso_value):
        self._iso = iso_value

    def isoformat(self):
        return self._iso


class FakeContract:
    def __init__(self, with_contact=True):
        self.__table__ = type("T", (), {})()
        setattr(
            self.__table__,
            "columns",
            [
                FakeColumn("id"),
                FakeColumn("client_id"),
                FakeColumn("amount_total"),
                FakeColumn("amount_due"),
                FakeColumn("is_signed"),
                FakeColumn("created_at"),
                FakeColumn("updated_at"),
            ],
        )
        self.id = 1
        self.client_id = 99
        self.amount_total = 1000.50
        self.amount_due = 500.25
        self.is_signed = True
        self.created_at = FakeDateTime("2023-01-01T00:00:00")
        self.updated_at = FakeDateTime("2023-01-02T00:00:00")
        self.client_name = "Agence Est"
        self.sales_contact_name = "Alice" if with_contact else ""


@pytest.fixture
def fake_contract():
    return FakeContract(with_contact=True)


def test_serialize_basic(fake_contract):
    serializer = ContractSerializer()
    with patch.object(serializer.valid, "validate_currency") as mock_curr:
        result = serializer.serialize(fake_contract)

    # Vérifie que les champs publics sont présents
    for field in ContractSerializer.PUBLIC_FIELDS:
        assert field in result

    # Vérifie les champs calculés
    assert result["sales_contact_name"] == "Alice"
    assert result["client_name"] == "Agence Est"

    # Vérifie que validate_currency a bien été appelé sur les montants
    assert mock_curr.call_count == 2


def test_serialize_no_contact():
    contract = FakeContract(with_contact=False)
    serializer = ContractSerializer()
    result = serializer.serialize(contract)  # type: ignore
    assert result["sales_contact_name"] == "Aucun contact"


def test_serialize_with_extra(fake_contract):
    serializer = ContractSerializer()
    result = serializer.serialize(fake_contract, extra={"extra": "value"})
    assert result["extra"] == "value"


def test_serialize_none_contract():
    serializer = ContractSerializer()
    assert serializer.serialize(None) == {}  # type: ignore


def test_serialize_list(fake_contract):
    serializer = ContractSerializer()
    result = serializer.serialize_list([fake_contract, None])  # type: ignore
    assert isinstance(result, list)
    assert result[0]["id"] == 1
