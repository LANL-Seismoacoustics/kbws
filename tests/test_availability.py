"""Tests for the FDSN availability service endpoints."""
from types import SimpleNamespace

from fastapi.testclient import TestClient
from obspy import UTCDateTime
from pisces.fdsn import Client

from kbws.main import app


ENDPOINT = "/fdsnws/availability/1"
client = TestClient(app)


def test_extent_response(monkeypatch):
    """Return availability extents as FDSN text."""
    row = SimpleNamespace(
        network="IU",
        station="ANMO",
        location="--",
        channel="BHZ",
        quality="-",
        samplerate=20.0,
        earliest=UTCDateTime("2010-01-01"),
        latest=UTCDateTime("2010-01-02"),
        updated=None,
        timespans=2,
        restriction="PARTIAL",
    )

    class Result:
        def all(self):
            return [row]

    def get_extent(*args, **kwargs):
        return Result()

    monkeypatch.setattr(Client, "get_extent", get_extent, raising=False)

    response = client.get(
        f"{ENDPOINT}/extent?starttime=2010-01-01&endtime=2010-01-03"
        "&network=IU&station=ANMO&location=--&channel=BHZ"
    )

    assert response.status_code == 200
    assert response.text.startswith(
        "#Network Station Location Channel Quality SampleRate Earliest Latest Updated"
    )
    assert "IU ANMO -- BHZ - 20.0" in response.text


def test_query_response(monkeypatch):
    """Return availability spans as FDSN text."""
    row = SimpleNamespace(
        network="IU",
        station="ANMO",
        location="--",
        channel="BHZ",
        samplerate=20.0,
        earliest=UTCDateTime("2010-01-01"),
        latest=UTCDateTime("2010-01-02"),
    )

    def get_availability(*args, **kwargs):
        return [row]

    monkeypatch.setattr(Client, "get_availability", get_availability, raising=False)

    response = client.get(
        f"{ENDPOINT}/query?starttime=2010-01-01&endtime=2010-01-03"
        "&network=IU&station=ANMO&location=--&channel=BHZ"
    )

    assert response.status_code == 200
    assert response.text.startswith(
        "#Network Station Location Channel Quality SampleRate Earliest Latest\n"
    )
    assert "IU ANMO -- BHZ - 20.0" in response.text


def test_json_response(monkeypatch):
    """Return availability rows as JSON."""
    row = SimpleNamespace(
        network="IU", station="ANMO", location="--", channel="BHZ",
        samplerate=20.0,
        earliest=UTCDateTime("2010-01-01"), latest=UTCDateTime("2010-01-02"),
    )

    def get_availability(*args, **kwargs):
        return [row]

    monkeypatch.setattr(Client, "get_availability", get_availability, raising=False)
    response = client.get(
        f"{ENDPOINT}/query?starttime=2010-01-01&endtime=2010-01-03"
        "&network=IU&station=ANMO&location=--&channel=BHZ&format=json"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == [{
        "network": "IU",
        "station": "ANMO",
        "location": "--",
        "channel": "BHZ",
        "quality": None,
        "samplerate": 20.0,
        "earliest": "2010-01-01T00:00:00.000000Z",
        "latest": "2010-01-02T00:00:00.000000Z",
    }]


def test_request_response(monkeypatch):
    """Return availability spans as FDSN request lines."""
    row = SimpleNamespace(
        network="IU", station="ANMO", location="--", channel="BHZ",
        earliest=UTCDateTime("2010-01-01"), latest=UTCDateTime("2010-01-02"),
    )

    def get_availability(*args, **kwargs):
        return [row]

    monkeypatch.setattr(Client, "get_availability", get_availability, raising=False)
    response = client.get(
        f"{ENDPOINT}/query?starttime=2010-01-01&endtime=2010-01-03"
        "&network=IU&station=ANMO&location=--&channel=BHZ&format=request"
    )

    assert response.status_code == 200
    assert response.text == (
        "IU ANMO -- BHZ 2010-01-01T00:00:00.000000Z "
        "2010-01-02T00:00:00.000000Z\n"
    )


def test_query_updated(monkeypatch):
    """Include the update column when requested."""
    row = SimpleNamespace(
        network="IU",
        station="ANMO",
        location="--",
        channel="BHZ",
        samplerate=20.0,
        earliest=UTCDateTime("2010-01-01"),
        latest=UTCDateTime("2010-01-02"),
        updated=UTCDateTime("2010-01-03"),
    )

    def get_availability(*args, **kwargs):
        return [row]

    monkeypatch.setattr(Client, "get_availability", get_availability, raising=False)

    response = client.get(
        f"{ENDPOINT}/query?starttime=2010-01-01&endtime=2010-01-03"
        "&network=IU&station=ANMO&location=--&channel=BHZ&show=latestupdate"
    )

    assert response.status_code == 200
    assert response.text.splitlines()[0].endswith("Updated")
    assert "2010-01-03T00:00:00.000000Z" in response.text


def test_nodata(monkeypatch):
    """Return the requested status when no availability matches."""
    def get_availability(*args, **kwargs):
        return []

    monkeypatch.setattr(Client, "get_availability", get_availability, raising=False)
    query = (
        f"{ENDPOINT}/query?starttime=2010-01-01&endtime=2010-01-03"
        "&network=IU&station=ANMO&location=--&channel=BHZ"
    )

    assert client.get(query).status_code == 204
    assert client.get(f"{query}&nodata=404").status_code == 404


def test_backend_error(monkeypatch):
    """Return an FDSN error for backend validation failures."""
    def fail(*args, **kwargs):
        raise ValueError("bad availability request")

    monkeypatch.setattr(Client, "get_extent", fail, raising=False)
    response = client.get(
        f"{ENDPOINT}/extent?starttime=2010-01-01&endtime=2010-01-03"
        "&network=IU&station=ANMO&location=--&channel=BHZ"
    )

    assert response.status_code == 400
    assert "bad availability request" in response.text


def test_extent_post(monkeypatch):
    """Return extent rows for POST selections."""
    row = SimpleNamespace(
        network="IU", station="ANMO", location="--", channel="BHZ",
        quality="-", samplerate=20.0,
        earliest=UTCDateTime("2010-01-01"), latest=UTCDateTime("2010-01-02"),
        updated=None, timespans=1, restriction="PARTIAL",
    )

    class Result:
        def all(self):
            return [row]

    def get_extent(*args, **kwargs):
        return Result()

    monkeypatch.setattr(Client, "get_extent", get_extent, raising=False)
    body = "IU ANMO -- BHZ 2010-01-01 2010-01-03\n"
    response = client.post(f"{ENDPOINT}/extent", content=body)

    assert response.status_code == 200
    assert "IU ANMO -- BHZ" in response.text


def test_query_post(monkeypatch):
    """Return query rows for POST selections."""
    row = SimpleNamespace(
        network="IU", station="ANMO", location="--", channel="BHZ",
        samplerate=20.0,
        earliest=UTCDateTime("2010-01-01"), latest=UTCDateTime("2010-01-02"),
        updated=UTCDateTime("2010-01-03"),
    )

    def get_availability(*args, **kwargs):
        return [row]

    monkeypatch.setattr(Client, "get_availability", get_availability, raising=False)
    body = "show=latestupdate\nIU ANMO -- BHZ 2010-01-01 2010-01-03\n"
    response = client.post(f"{ENDPOINT}/query", content=body)

    assert response.status_code == 200
    assert response.text.splitlines()[0].endswith("Updated")


def test_request_post(monkeypatch):
    """Return POST availability results as request lines."""
    row = SimpleNamespace(
        network="IU", station="ANMO", location="--", channel="BHZ",
        earliest=UTCDateTime("2010-01-01"), latest=UTCDateTime("2010-01-02"),
    )

    def get_availability(*args, **kwargs):
        return [row]

    monkeypatch.setattr(Client, "get_availability", get_availability, raising=False)
    body = (
        "format=request\n"
        "IU ANMO -- BHZ 2010-01-01 2010-01-03\n"
    )
    response = client.post(f"{ENDPOINT}/query", content=body)

    assert response.status_code == 200
    assert response.text == (
        "IU ANMO -- BHZ 2010-01-01T00:00:00.000000Z "
        "2010-01-02T00:00:00.000000Z\n"
    )


def test_post_bad_input():
    """Reject malformed POST selection lines."""
    response = client.post(
        f"{ENDPOINT}/query",
        content="IU ANMO BHZ 2010-01-01 2010-01-03\n",
    )

    assert response.status_code == 400
    assert "Error 400: Badly formed request." in response.text


def test_post_limit():
    """Reject POST bodies over the line limit."""
    body = "\n".join("IU ANMO -- BHZ 2010-01-01 2010-01-03" for _ in range(101))
    response = client.post(f"{ENDPOINT}/query", content=body)

    assert response.status_code == 413
    assert "100-line limit" in response.text
