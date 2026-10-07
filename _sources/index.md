# KBWS

FDSN Web Services for CSS-like SQL Databases

---

KBWS connects your CSS-like SQL database (CSS 3.0, KB Core) to the FDSN Web Services standard.

**Leverage standard protocols for seismological data access**  
Use any FDSN-WS or REST API client (like ObsPy or [Restish](https://rest.sh)) as the interface with your database, instead of using SQL on a connected server or some other programmatic interface (like Pisces) directly.
Clients like the [ObsPy FDSN Client](https://docs.obspy.org/packages/obspy.clients.fdsn.html), `curl`, or just your web browser become viable ways to acquire data, no home-grown software installations required!

**Built on modern, open-source technologies**  
KBWS uses [FastAPI](https://fastapi.tiangolo.com/), [Pisces](https://github.com/LANL-Seismoacoustics/pisces), [SQLAlchemy](http://www.sqlalchemy.org), and [ObsPy](http://www.obspy.org) to provide a fast, standards-compliant web service layer over your existing database infrastructure.

**Flexible deployment options**  
Run KBWS natively with Conda/pip, or deploy it in containers using Docker or Podman. Configure multiple database schemas, waveform directories, and table mappings through simple environment files.


## Features

* Complete implementation of FDSN web service standards:
  * **fdsnws-event**: Query and retrieve event catalogs in QuakeML, JSON, or CSV formats
  * **fdsnws-station**: Query station metadata with full channel-level detail
  * **fdsnws-dataselect**: Retrieve waveform data in MiniSEED or SAC formats
  * **fdsnws-availability**: Query waveform data availability
* Direct integration with [ObsPy](http://www.obspy.org) FDSN client
* Support for Oracle databases via cx_Oracle or oracledb drivers
* Flexible schema mapping - configure any table names via environment variables
* Geographic and temporal filtering using native SQL queries
* Container-ready with rootless Podman support


## Quick Start

### Start the server

`uvicorn kbws.main:app --host 0.0.0.0 --port 8000`

### Using ObsPy

```python
from obspy.clients.fdsn import Client

# Connect to your KBWS instance
client = Client('http://localhost:8000', _discover_services=False)

# Query events
catalog = client.get_events(
    starttime="2012-11-01",
    endtime="2012-11-03",
    minlatitude=40,
    maxlatitude=47
)

# Get waveforms
stream = client.get_waveforms(
    network="IU",
    station="ANMO",
    location="00",
    channel="BH?",
    starttime="2012-11-01T00:00:00",
    endtime="2012-11-01T01:00:00"
)
```

### Using curl

```bash
# Get events as QuakeML
curl "http://localhost:8000/fdsnws/event/1/query?starttime=2012-11-01&endtime=2012-11-03&minlatitude=40&maxlatitude=47"

# Get waveforms as MiniSEED
curl "http://localhost:8000/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2012-11-01T00:00:00&end=2012-11-01T01:00:00" -o data.mseed
```


```{toctree}
:hidden: true

installation.md
deployment.md
development.md
```

```{toctree}
:hidden: true
:caption: Reference

about/changelog.md
about/license.md
API Documentation <api/modules.rst>
```
