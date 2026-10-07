from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pisces.schema.kbcore as kb

from .config import Settings

# automatically loads settings from .env file
settings = Settings()

# # XXX: this block is for oracledb on MacOS.  Linux and use cx_oracle and oracle-instant-client
# import oracledb
# oracledb.init_oracle_client(lib_dir='/opt/oracle/instantclient_23_3')
# # XXX: kludge for sqlalchemy 1.4
# import sys
# oracledb.version = "8.3.0"
# sys.modules["cx_Oracle"] = oracledb

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


class Affiliation(kb.Affiliation):
    __tablename__ = settings.affiliation


class Amplitude(kb.Amplitude):
    __tablename__ = settings.amplitude


class Arrival(kb.Arrival):
    __tablename__ = settings.arrival


class Assoc(kb.Assoc):
    __tablename__ = settings.assoc


class Event(kb.Event):
    __tablename__ = settings.event


class Gregion(kb.Gregion):
    __tablename__ = settings.gregion


class Instrument(kb.Instrument):
    __tablename__ = settings.instrument


class Lastid(kb.Lastid):
    __tablename__ = settings.lastid


class Netmag(kb.Netmag):
    __tablename__ = settings.netmag


class Network(kb.Network):
    __tablename__ = settings.network


class Origerr(kb.Origerr):
    __tablename__ = settings.origerr


class Origin(kb.Origin):
    __tablename__ = settings.origin


class Remark(kb.Remark):
    __tablename__ = settings.remark


class Sensor(kb.Sensor):
    __tablename__ = settings.sensor


class Site(kb.Site):
    __tablename__ = settings.site


class Sitechan(kb.Sitechan):
    __tablename__ = settings.sitechan


class Sregion(kb.Sregion):
    __tablename__ = settings.sregion


class Stamag(kb.Stamag):
    __tablename__ = settings.stamag


class Wfdisc(kb.Wfdisc):
    __tablename__ = settings.wfdisc


class Wftag(kb.Wftag):
    __tablename__ = settings.wftag
