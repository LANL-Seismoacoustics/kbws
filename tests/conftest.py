from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
import socket
import threading
import time

import pytest
import uvicorn

from pisces.tables.kbcore import Affiliation, Event, Origin, Wfdisc

from kbws.main import app

engine = create_engine(
    'sqlite:///:memory:',
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def fdsn_server():
    """Run the application on a local TCP port for real ObsPy discovery."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        host, port = sock.getsockname()

    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.01)
    if not server.started:
        server.should_exit = True
        thread.join(timeout=5)
        raise RuntimeError("Uvicorn did not start for ObsPy discovery test")

    yield f"http://{host}:{port}"

    server.should_exit = True
    thread.join(timeout=5)


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
