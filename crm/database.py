from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config.settings import get_database_url

Base = declarative_base()
engine = create_engine(get_database_url())
SessionLocal = sessionmaker(bind=engine)
