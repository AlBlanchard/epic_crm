import sqlite3, pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from crm.database import Base
from crm import models  # Charge les classes sinon ne fonctionne pas

TEST_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(TEST_URL, echo=False, future=True)


# Ajoute le PRAGMA sur toutes les connexions
@event.listens_for(engine, "connect")
def _enable_fk(dbapi_connection, _):
    if isinstance(dbapi_connection, sqlite3.Connection):
        dbapi_connection.execute("PRAGMA foreign_keys = ON")


# Crée les tables après avoir activé les FK
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


#  Fixtures
@pytest.fixture(scope="session")
def engine_fixture():
    return engine


@pytest.fixture(scope="function")
def db_session(engine_fixture):
    Session = sessionmaker(bind=engine_fixture, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
