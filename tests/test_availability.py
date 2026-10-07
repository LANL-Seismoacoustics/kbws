"""
Tests for the availability service endpoint.

Availability service provides information about data availability and quality
for time series data following the FDSN availability web service specification.
"""
import pytest
from fastapi.testclient import TestClient

from pisces.fdsn import Client
from kbws.main import app

ENDPOINT = "/fdsnws/availability/1/query?"

client = TestClient(app)


# TODO: Add availability-specific fixtures when tests are implemented
# For example:
# @pytest.fixture(scope='function')
# def get_availability(monkeypatch):
#     """Patch availability queries."""
#     pass


# TODO: Implement availability service tests
# Examples:
# def test_availability_query(get_availability):
#     """Test availability query response."""
#     response = client.get(f"{ENDPOINT}network=IU&station=ANMO")
#     assert response.status_code == 200
#
# def test_availability_extent(get_availability):
#     """Test availability extent query."""
#     response = client.get(f"{ENDPOINT}extent=true")
#     assert response.status_code == 200
