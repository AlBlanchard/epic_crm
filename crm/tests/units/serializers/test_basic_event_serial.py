import pytest
from crm.serializers.event_serializer import EventSerializer, EventNoteSerializer


class FakeColumn:
    def __init__(self, name):
        self.name = name


class FakeDateTime:
    def __init__(self, iso_value):
        self._iso = iso_value

    def isoformat(self):
        return self._iso


class FakeInnerClient:
    def __init__(self):
        self.email = "client@example.com"
        self.phone = "0102030405"


class FakeClient:
    def __init__(self):
        self.client_name = "Agence Est"
        self.client = FakeInnerClient()


class FakeSupport:
    def __init__(self):
        self.username = "SupportUser"


class FakeNote:
    def __init__(self, note_text="Test note"):
        self.note = note_text
        self.id = 1
        self.event_id = 42
        self.created_at = FakeDateTime("2023-01-03T00:00:00")
        self.__table__ = type("T", (), {})()
        setattr(
            self.__table__,
            "columns",
            [
                FakeColumn("id"),
                FakeColumn("event_id"),
                FakeColumn("note"),
                FakeColumn("created_at"),
            ],
        )


class FakeEvent:
    def __init__(self, with_relations=True):
        self.__table__ = type("T", (), {})()
        setattr(
            self.__table__,
            "columns",
            [
                FakeColumn("id"),
                FakeColumn("contract_id"),
                FakeColumn("support_contact_id"),
                FakeColumn("date_start"),
                FakeColumn("date_end"),
                FakeColumn("location"),
                FakeColumn("attendees"),
                FakeColumn("created_at"),
                FakeColumn("updated_at"),
            ],
        )
        self.id = 1
        self.contract_id = 99
        self.support_contact_id = 77
        self.date_start = FakeDateTime("2023-01-10T10:00:00")
        self.date_end = FakeDateTime("2023-01-10T12:00:00")
        self.location = "Paris"
        self.attendees = "10"
        self.created_at = FakeDateTime("2023-01-01T00:00:00")
        self.updated_at = FakeDateTime("2023-01-02T00:00:00")

        if with_relations:
            self.contract = FakeClient()
            self.support_contact = FakeSupport()
            self.notes = [FakeNote("Note 1"), FakeNote("Note 2")]
        else:
            self.contract = None
            self.support_contact = None
            self.notes = None


# -------- EventSerializer --------
@pytest.fixture
def fake_event():
    return FakeEvent(with_relations=True)


def test_event_serialize_basic(fake_event):
    serializer = EventSerializer()
    result = serializer.serialize(fake_event)

    # Champs publics
    for field in EventSerializer.PUBLIC_FIELDS:
        assert field in result

    # Champs calculés
    assert result["client_name"] == "Agence Est"
    assert result["client_contact"] == ["client@example.com", "0102030405"]
    assert result["support_contact_name"] == "SupportUser"
    assert result["notes"] == ["Note 1", "Note 2"]


def test_event_serialize_no_relations():
    serializer = EventSerializer()
    result = serializer.serialize(FakeEvent(with_relations=False))  # type: ignore

    assert result["client_name"] == "Aucun"
    assert result["support_contact_name"] == "Aucun"
    assert result["notes"] == "Aucun"


def test_event_serialize_with_extra(fake_event):
    serializer = EventSerializer()
    result = serializer.serialize(fake_event, extra={"extra": "value"})
    assert result["extra"] == "value"


def test_event_serialize_none():
    serializer = EventSerializer()
    assert serializer.serialize(None) == {}  # type: ignore


def test_event_serialize_list(fake_event):
    serializer = EventSerializer()
    result = serializer.serialize_list([fake_event, None])  # type: ignore
    assert isinstance(result, list)
    assert result[0]["id"] == 1


# -------- EventNoteSerializer --------
@pytest.fixture
def fake_note():
    return FakeNote("Hello Note")


def test_event_note_serialize_basic(fake_note):
    serializer = EventNoteSerializer()
    result = serializer.serialize(fake_note)

    for field in EventNoteSerializer.PUBLIC_FIELDS:
        assert field in result

    assert result["note"] == "Hello Note"


def test_event_note_serialize_none():
    serializer = EventNoteSerializer()
    assert serializer.serialize(None) == {}  # type: ignore


def test_event_note_serialize_list(fake_note):
    serializer = EventNoteSerializer()
    result = serializer.serialize_list([fake_note, None])  # type: ignore
    assert isinstance(result, list)
    assert result[0]["note"] == "Hello Note"
