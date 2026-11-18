"""Tests for the FDSN station service endpoints."""

from fastapi.testclient import TestClient
from obspy.core.inventory import Inventory, Network, Site, Station
from pisces.fdsn import Client

from kbws import database as db
from kbws.config import settings
from kbws.main import app

client = TestClient(app)
ENDPOINT = "/fdsnws/station/1"


def inventory():
    return Inventory(networks=[Network(
        code="IU",
        stations=[Station(
            code="ANMO",
            latitude=34.95,
            longitude=-106.46,
            elevation=1800,
            site=Site(name="Albuquerque"),
        )],
    )], source="test")


def test_station_without_response_tables(monkeypatch):
    """Basic station metadata works without response tables."""
    monkeypatch.setattr(settings, "sensor", None)
    monkeypatch.setattr(settings, "instrument", None)
    monkeypatch.setattr(Client, "get_stations", lambda *args, **kwargs: inventory(), raising=False)

    response = client.get(f"{ENDPOINT}/query?level=station")

    assert response.status_code == 200


def test_station_response_requires_tables(monkeypatch):
    """Response-level station metadata reports missing response tables."""
    monkeypatch.setattr(settings, "sensor", None)
    monkeypatch.setattr(settings, "instrument", None)

    response = client.get(f"{ENDPOINT}/query?level=response")

    assert response.status_code == 503
    assert "sensor" in response.text
    assert "instrument" in response.text


def test_station_xml_response(monkeypatch):
    captured = {}

    def get_stations(*args, **kwargs):
        captured.update(kwargs)
        return inventory()

    monkeypatch.setattr(Client, "get_stations", get_stations, raising=False)
    response = client.get(
        f"{ENDPOINT}/query?network=IU&station=ANMO&level=station"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert "ANMO" in response.text
    assert captured["level"] == "station"
    assert captured["network"] == "IU"


def test_station_text_response(monkeypatch):
    monkeypatch.setattr(Client, "get_stations", lambda *args, **kwargs: inventory(), raising=False)
    response = client.get(
        f"{ENDPOINT}/query?network=IU&station=ANMO&format=text"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "IU|ANMO|34.95|-106.46|1800.0|Albuquerque" in response.text


def test_station_format_sql(monkeypatch):
    class Statement:
        def compile(self, *args, **kwargs):
            return "SELECT * FROM site"

    class Query:
        statement = Statement()

    monkeypatch.setattr(Client, "get_stations", lambda *args, **kwargs: Query(), raising=False)
    response = client.get(f"{ENDPOINT}/query?format=sql")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "SELECT * FROM site"


def test_station_format_css(monkeypatch):
    class Query:
        def __iter__(self):
            return iter([type("Row", (), {db.Site.__name__: "site row"})()])

    monkeypatch.setattr(Client, "get_stations", lambda *args, **kwargs: Query(), raising=False)
    monkeypatch.setattr(
        "kbws.routes.station._get_entities",
        lambda query, name: (db.Site,),
    )
    response = client.get(f"{ENDPOINT}/query?format=css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "site row"


def test_station_post_text(monkeypatch):
    monkeypatch.setattr(Client, "get_stations", lambda *args, **kwargs: inventory(), raising=False)
    response = client.post(
        f"{ENDPOINT}/query",
        content="format=text\nlevel=station\nIU ANMO -- BHZ 2010-01-01 2010-01-02\n",
    )

    assert response.status_code == 200
    assert "IU|ANMO|34.95|-106.46|1800.0|Albuquerque" in response.text


def test_station_post_response_text_is_bad_request(monkeypatch):
    monkeypatch.setattr(Client, "get_stations", lambda *args, **kwargs: inventory(), raising=False)
    response = client.post(
        f"{ENDPOINT}/query",
        content="format=text\nlevel=response\nIU ANMO -- BHZ 2010-01-01 2010-01-02\n",
    )

    assert response.status_code == 400
    assert "format=text is not supported" in response.text


def test_station_post_css(monkeypatch):
    class Query:
        def __iter__(self):
            return iter([type("Row", (), {db.Site.__name__: "site row"})()])

    monkeypatch.setattr(Client, "get_stations", lambda *args, **kwargs: Query(), raising=False)
    monkeypatch.setattr("kbws.routes.station._get_entities", lambda query, name: (db.Site,))
    response = client.post(
        f"{ENDPOINT}/query",
        content="format=css\nIU ANMO -- BHZ 2010-01-01 2010-01-02\n",
    )

    assert response.status_code == 200
    assert response.text == "site row"


def test_station_post_sql(monkeypatch):
    class Statement:
        def compile(self, *args, **kwargs):
            return "SELECT * FROM site"

    class Query:
        statement = Statement()

    monkeypatch.setattr(Client, "get_stations", lambda *args, **kwargs: Query(), raising=False)
    response = client.post(
        f"{ENDPOINT}/query",
        content="format=sql\nIU ANMO -- BHZ 2010-01-01 2010-01-02\n",
    )

    assert response.status_code == 200
    assert response.text == "SELECT * FROM site"


def test_station_nodata(monkeypatch):
    monkeypatch.setattr(
        Client,
        "get_stations",
        lambda *args, **kwargs: Inventory(networks=[], source="test"),
        raising=False,
    )
    response = client.get(
        f"{ENDPOINT}/query?network=IU&station=ANMO&nodata=404"
    )

    assert response.status_code == 404
