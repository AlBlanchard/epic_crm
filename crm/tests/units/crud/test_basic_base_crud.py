import pytest
from unittest.mock import MagicMock
from crm.crud.base_crud import AbstractBaseCRUD


class FakeColumn:
    def __init__(self, name):
        self.name = name


class FakeModel:
    class __table__:
        columns = [FakeColumn("id"), FakeColumn("owner_id"), FakeColumn("name")]

    id = "id_column"
    owner_id = "owner_id_column"
    name = "name_column"


@pytest.fixture
def crud():
    return AbstractBaseCRUD(session=MagicMock())


def test_get_entities_no_filters(crud):
    fake_query = MagicMock()
    fake_query.all.return_value = ["entity1", "entity2"]
    crud.session.query.return_value = fake_query

    result = crud.get_entities(FakeModel)

    assert result == ["entity1", "entity2"]
    crud.session.query.assert_called_once_with(FakeModel)
    fake_query.all.assert_called_once()


def test_get_entities_with_eager_options(crud):
    fake_query = MagicMock()
    fake_query.options.return_value = fake_query
    fake_query.all.return_value = ["entity"]
    crud.session.query.return_value = fake_query

    result = crud.get_entities(FakeModel, eager_options=("opt1", "opt2"))

    assert result == ["entity"]
    fake_query.options.assert_called_once_with("opt1", "opt2")


def test_get_entities_with_owner_filter(crud):
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.all.return_value = ["entity"]
    crud.session.query.return_value = fake_query

    result = crud.get_entities(FakeModel, owner_field="owner_id", owner_id=42)

    assert result == ["entity"]
    fake_query.filter.assert_called_once()


def test_get_entities_with_filters(crud):
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.all.return_value = ["entity"]
    crud.session.query.return_value = fake_query

    result = crud.get_entities(FakeModel, filters={"name": "Alice"})

    assert result == ["entity"]
    fake_query.filter.assert_called_once()


def test_get_entities_ignore_invalid_filter(crud):
    fake_query = MagicMock()
    fake_query.filter.return_value = fake_query
    fake_query.all.return_value = ["entity"]
    crud.session.query.return_value = fake_query

    # invalid_field n'existe pas -> ne doit pas provoquer d'erreur
    result = crud.get_entities(FakeModel, filters={"invalid_field": "X"})

    assert result == ["entity"]
    fake_query.filter.assert_not_called()  # rien filtré car champ inexistant


def test_get_entities_with_order_by_raises(crud):
    with pytest.raises(ValueError):
        crud.get_entities(FakeModel, order_by="name")
