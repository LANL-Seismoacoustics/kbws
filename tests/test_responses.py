"""Tests for app-wide FDSN error response formatting (kbws.responses / kbws.main)."""
from fastapi.testclient import TestClient

from pisces.fdsn import Client

from kbws.main import app
from kbws.responses import fdsn_error_response, _TEMPLATE, BAD_REQUEST, NO_DATA_ALT

ENDPOINT = "/fdsnws/event/1/query?"

# raise_server_exceptions=False so the TestClient returns the handled response instead
# of re-raising the exception the handler is supposed to catch.
client = TestClient(app, raise_server_exceptions=False)


def test_validation_error_response_is_fdsn_formatted():
    """A bad query param (handled by RequestValidationError) returns the FDSN error template."""
    response = client.get(f"{ENDPOINT}maxlatitude=not-a-number")
    assert response.status_code == 400
    request_id = response.headers["X-Request-ID"]
    body = response.content.decode("utf-8")
    assert f"Request ID: {request_id}" in body
    assert body.startswith(_TEMPLATE.split("{")[0])
    assert "Error 400: Badly formed request." in body


def test_unhandled_exception_returns_fdsn_formatted_500(monkeypatch):
    """An unhandled exception from a route is caught and returned as a formatted 500."""
    def raise_error(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(Client, "get_events", raise_error)

    response = client.get(
        (
            f"{ENDPOINT}"
            "maxdepth=100&maxlatitude=47&maxlongitude=5&mindepth=1.3&minlatitude=40&minlongitude=-10"
        )
    )
    assert response.status_code == 500
    request_id = response.headers["X-Request-ID"]
    body = response.content.decode("utf-8")
    assert body.startswith(_TEMPLATE.split("{")[0])
    assert "Error 500: Internal server error." in body
    assert f"Request ID: {request_id}" in body
    assert "Include this ID when contacting the service operator." in body
    assert "boom" not in body


def test_fdsn_error_response_format():
    """fdsn_error_response renders the exact standard FDSN plain-text error template."""
    from obspy import UTCDateTime
    from starlette.requests import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/fdsnws/event/1/query",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("testserver", 80),
    }
    request = Request(scope)

    utc_now = UTCDateTime()
    r = fdsn_error_response(request, BAD_REQUEST, detail="bad input", service_version="1.2.0")
    expected = _TEMPLATE.format(
        code=BAD_REQUEST.code,
        simple_descr=BAD_REQUEST.message,
        detail="bad input",
        service_docs_uri=request.base_url,
        submitted_url=str(request.url),
        utc_date_time=utc_now,
        service_version="1.2.0",
    )
    assert r.status_code == 400
    body = r.body.decode("utf-8")
    # everything but the timestamp line must match exactly
    assert body.split("Request Submitted:")[0] == expected.split("Request Submitted:")[0]

    r2 = fdsn_error_response(request, NO_DATA_ALT, detail="", service_version="1.2.0")
    assert r2.status_code == 404
