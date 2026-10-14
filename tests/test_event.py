import io

from fastapi.testclient import TestClient
from obspy import read_events, UTCDateTime

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


@pytest.fixture(scope='function')
def capture_get_events_kwargs(monkeypatch):
    """Patch Client.get_events to capture the kwargs it was called with, and return the example Catalog."""
    captured = {}

    def mock_get_events(self, *args, **kwargs):
        captured.update(kwargs)
        return cat

    monkeypatch.setattr(Client, 'get_events', mock_get_events)
    return captured


def test_event_query_param_conversion(capture_get_events_kwargs):
    """Verify route-level parameter conversions passed to Client.get_events."""
    response = client.get(
        (
            f"{ENDPOINT}"
            "starttime=2012-11-01T00:00:00&endtime=2012-11-03T01:00:00&updatedafter=2012-11-02"
            "&minlongitude=-10&maxlongitude=5&minlatitude=40&maxlatitude=47"
            "&mindepth=1.3&maxdepth=100&minmagnitude=2&maxmagnitude=8&magnitudetype=mb"
            "&eventtype=earthquake&includeallorigins=true&includeallmagnitudes=true"
            "&preferredmagnitude=mw,ms&includearrivals=true&eventid=1234&contributor=ISC"
            "&format=xml"
        )
    )
    assert response.status_code == 200

    kwargs = capture_get_events_kwargs
    assert kwargs['starttime'] == UTCDateTime("2012-11-01T00:00:00")
    assert kwargs['endtime'] == UTCDateTime("2012-11-03T01:00:00")
    assert kwargs['updatedafter'] == UTCDateTime("2012-11-02")
    assert kwargs['minlongitude'] == -10
    assert kwargs['maxlongitude'] == 5
    assert kwargs['minlatitude'] == 40
    assert kwargs['maxlatitude'] == 47
    assert kwargs['mindepth'] == 1.3
    assert kwargs['maxdepth'] == 100
    assert kwargs['minmagnitude'] == 2
    assert kwargs['maxmagnitude'] == 8
    assert kwargs['magnitudetype'] == 'mb'
    assert kwargs['eventtype'] == 'earthquake'
    assert kwargs['includeallorigins'] is True
    assert kwargs['includeallmagnitudes'] is True
    assert kwargs['preferred_magnitude'] == ('mw', 'ms')
    assert kwargs['includearrivals'] is True
    assert kwargs['eventid'] == '1234'
    assert kwargs['contributor'] == 'ISC'
    assert kwargs['asquery'] is False


def test_event_query_defaults(capture_get_events_kwargs):
    """Unset optional params convert to None/defaults, not missing or empty-string."""
    response = client.get(ENDPOINT)
    assert response.status_code == 200

    kwargs = capture_get_events_kwargs
    assert kwargs['starttime'] is None
    assert kwargs['endtime'] is None
    assert kwargs['updatedafter'] is None
    assert kwargs['preferred_magnitude'] == ("mb", "mw", "ms")
    assert kwargs['includeallmagnitudes'] is False
    assert kwargs['includeallorigins'] is False
    assert kwargs['includearrivals'] is False
    assert kwargs['eventid'] is None
    assert kwargs['contributor'] is None


def test_event_nodata_204_default(monkeypatch):
    """No results and default nodata param returns 204."""
    monkeypatch.setattr(Client, 'get_events', lambda self, *a, **k: None)
    response = client.get(ENDPOINT)
    assert response.status_code == 204


def test_event_nodata_404(monkeypatch):
    """No results with nodata=404 returns 404."""
    monkeypatch.setattr(Client, 'get_events', lambda self, *a, **k: None)
    response = client.get(f"{ENDPOINT}nodata=404")
    assert response.status_code == 404


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
