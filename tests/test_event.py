import io

from fastapi.testclient import TestClient
from obspy import read_events

from pisces.tables.kbcore import Event, Origin
from pisces.fdsn import Client
from pisces.util import literal_sql

import pytest

from kbws.main import app

ENDPOINT = "/fdsnws/event/1/query?"

client = TestClient(app)

cat = read_events()


@pytest.fixture(scope='function')
def get_events_catalog(monkeypatch):
    """ Patch pisces.fdsn.Client.get_events to always return ObsPy's example Catalog."""
    def mock_get_events(*args, **kwargs):
        return cat

    # replace Client.get_events with the mock
    monkeypatch.setattr(Client, 'get_events', mock_get_events)


@pytest.fixture(scope='function')
def get_events_query(monkeypatch, db_session):
    """ Patch pisces.fdsn.Client.get_events to always return a SQLite joined Event+Origin query."""

    def mock_get_events(*args, **kwargs):
        # return a SQLAlchemy Query instance
        return db_session.query(Event, Origin).filter(Event.evid == Origin.evid)

    # replace Client.get_events with the mock
    monkeypatch.setattr(Client, 'get_events', mock_get_events)


def test_event_format_xml(get_events_catalog):
    """ Test for proper XML response."""
    with io.BytesIO() as fh:
        cat.write(fh, format='QUAKEML')
        fh.seek(0)
        xml_cat = fh.read()

    response = client.get(
        (
            f"{ENDPOINT}"
            "maxdepth=100&maxlatitude=47&maxlongitude=5&mindepth=1.3&minlatitude=40&minlongitude=-10"
            "&format=xml"
        )
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/xml'
    assert response.content == xml_cat


def test_event_format_json(get_events_catalog):
    """ Test for proper JSON response."""
    with io.StringIO() as fh:
        cat.write(fh, format='JSON')
        fh.seek(0)
        json_cat = fh.read()

    response = client.get(
        (
            f"{ENDPOINT}"
            "maxdepth=100&maxlatitude=47&maxlongitude=5&mindepth=1.3&minlatitude=40&minlongitude=-10"
            "&format=json"
        )
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/json'
    assert response.content == json_cat.encode('utf-8')


def test_event_format_sql(get_events_query, db_session):
    """ Test for proper SQL response."""
    sql = literal_sql(
        db_session.query(Event, Origin).filter(Event.evid == Origin.evid)
    )
    response = client.get(
        (
            f"{ENDPOINT}"
            "maxdepth=100&maxlatitude=47&maxlongitude=5&mindepth=1.3&minlatitude=40&minlongitude=-10"
            "&format=sql"
        )
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
    assert response.content == sql.encode('utf-8')


def test_event_format_css(get_events_query, db_session):
    """ Test for proper CSS Origin flat file response."""
    origin = Origin(lat=1, lon=2, orid=3, evid=4)
    event = Event(evid=4)
    db_session.add_all([event, origin])
    db_session.commit()

    response = client.get(
        (
            f"{ENDPOINT}"
            "maxdepth=100&maxlatitude=47&maxlongitude=5&mindepth=1.3&minlatitude=40&minlongitude=-10"
            "&format=css"
        )
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
    assert response.content == str(origin).encode('utf-8')


def test_event_format_bad():
    """ Test for unsupported formats . """
    # with pytest.raises(Exception):
    response = client.get(
        (
            f"{ENDPOINT}"
            "maxdepth=100&maxlatitude=47&maxlongitude=5&mindepth=1.3&minlatitude=40&minlongitude=-10"
            "&format=bad"
        )
    )
    # Badly formed request.
    assert response.status_code == 400
