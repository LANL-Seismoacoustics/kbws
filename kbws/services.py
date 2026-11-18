"""Service capability checks based on configured database tables."""
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
