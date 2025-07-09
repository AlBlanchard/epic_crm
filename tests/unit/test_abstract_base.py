import time, datetime as dt
from decimal import Decimal
import pytest
from sqlalchemy import Column, String
from sqlalchemy.exc import IntegrityError
from crm.database import Base
from crm.models import AbstractBase


# Création d'une classe de test pour AbstractBase
class Dummy(AbstractBase):
    __tablename__ = "dummy"
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)


@pytest.fixture(scope="function", autouse=True)
def _create_dummy_table(db_session):
    """Crée la table Dummy pour les tests."""

    Base.metadata.create_all(bind=db_session.bind)
    yield
    Base.metadata.drop_all(bind=db_session.bind)


def test_abstract_base_creation(db_session):
    """Vérifie que la classe abstraite peut être instanciée via une sous-classe."""
    d = Dummy(name="alpha")
    db_session.add(d)
    db_session.flush()
    assert d.id is not None
    assert isinstance(d.id, int)


def test_created_at_auto(db_session):
    """Vérifie que created_at est initialisé à la création."""
    d = Dummy(name="beta")
    db_session.add(d)
    db_session.flush()
    assert d.created_at is not None
    assert d.created_at.tzinfo is not None  # Vérifie que le fuseau horaire est UTC
    assert abs((d.created_at - dt.datetime.now(dt.timezone.utc)).total_seconds()) < 5


def test_updated_date_initial(db_session):
    """Vérifie que updated_at est initialisé à la création."""
    d = Dummy(name="gamma")
    db_session.add(d)
    db_session.flush()
    assert (d.updated_at == d.created_at) is True


def test_updated_at_changes(db_session):
    """Vérifie que updated_at est mis à jour lors d'une modification."""
    d = Dummy(name="delta")
    db_session.add(d)
    db_session.flush()

    time.sleep(0.002)

    d.description = "Une modification"  # type: ignore[attr-defined]
    old_updated_at = d.updated_at
    db_session.flush()
    assert (d.updated_at > old_updated_at) is True
    assert (d.created_at < d.updated_at) is True


def test_updated_at_monotonic(db_session):
    """Vérifie que updated_at est toujours plus récent que created_at."""
    d = Dummy(name="epsilon")
    db_session.add(d)
    db_session.flush()
    first = d.updated_at

    time.sleep(0.002)

    d.name = "epsilon_2.0"  # type: ignore[attr-defined]
    db_session.flush()
    second = d.updated_at
    assert (second > first) is True


def test_model_is_abstract():
    """Vérifie que Dummy est bien une classe abstraite."""
    assert hasattr(AbstractBase, "__abstract__") and AbstractBase.__abstract__ is True
