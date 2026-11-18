import pisces.schema.kbcore as kb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import Settings

# automatically loads settings from .env file
settings = Settings()

if settings.oracle_client_lib_dir:
    import oracledb

    oracledb.init_oracle_client(lib_dir=settings.oracle_client_lib_dir)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# make

# Threadsafe local db session dependency for endpoints
def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _model(base, table_name):
    """Create a mapped model only when its table is configured."""
    return type(base.__name__, (base,), {"__tablename__": table_name}) if table_name else None


Affiliation = _model(kb.Affiliation, settings.affiliation)
Arrival = _model(kb.Arrival, settings.arrival)
Assoc = _model(kb.Assoc, settings.assoc)
Event = _model(kb.Event, settings.event)
Instrument = _model(kb.Instrument, settings.instrument)
Netmag = _model(kb.Netmag, settings.netmag)
Network = _model(kb.Network, settings.network)
Origin = _model(kb.Origin, settings.origin)
Sensor = _model(kb.Sensor, settings.sensor)
Site = _model(kb.Site, settings.site)
Sitechan = _model(kb.Sitechan, settings.sitechan)
Wfdisc = _model(kb.Wfdisc, settings.wfdisc)
