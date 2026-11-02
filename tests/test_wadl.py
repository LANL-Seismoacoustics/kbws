"""Tests for FDSN WADL service discovery."""

from obspy.clients.fdsn import Client


def test_wadl_obspy_client_discovery(fdsn_server):
    """ObsPy discovers the event and dataselect services from the WADLs."""
    discovered = Client(fdsn_server)

    assert "event" in discovered.services
    assert "dataselect" in discovered.services
