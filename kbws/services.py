"""Guard FDSN routes using the tables configured for each service.

A service returns FDSN-formatted ``503`` responses when its required tables
are not configured, allowing one deployment to expose only supported
services or detail levels.
"""
from .config import settings

SERVICE_TABLES = {
    "availability": {"affiliation", "wfdisc", "site", "network"},
    "dataselect": {"affiliation", "wfdisc"},
    "event": {"event", "origin", "netmag"},
    "station": {"affiliation", "network", "site"},
}


class ServiceUnavailable(Exception):
    def __init__(self, service: str, missing_tables: set[str]):
        self.service = service
        self.missing_tables = sorted(missing_tables)


def require_tables(service: str, tables: set[str]):
    missing = {name for name in tables if not getattr(settings, name)}
    if missing:
        raise ServiceUnavailable(service, missing)


def require_service(service: str):
    def guard():
        require_tables(service, SERVICE_TABLES[service])

    return guard
