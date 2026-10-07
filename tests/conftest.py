from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import pytest

from pisces.tables.kbcore import Affiliation, Event, Origin, Wfdisc

engine = create_engine(
    'sqlite:///:memory:',
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    Origin.__table__.create(engine)
    Event.__table__.create(engine)
    Wfdisc.__table__.create(engine)
    Affiliation.__table__.create(engine)
    session = SessionLocal()

    yield session

    session.rollback()
    session.close()
    Origin.__table__.drop(engine)
    Event.__table__.drop(engine)
    Wfdisc.__table__.drop(engine)
    Affiliation.__table__.drop(engine)
