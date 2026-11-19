# KBWS: FDSN Web Services for CSS-like SQL Databases

Have a CSS-like SQL database (CSS 3.0, KB Core), and wish it had an [FDSN Web Services](https://www.fdsn.org/webservices/) endpoint?
This package uses [FastAPI](https://fastapi.tiangolo.com/) and [Pisces](https://github.com/LANL-Seismoacoustics/pisces) to provide a FDSN-WS on your CSS database.

## Service support

KBWS provides FDSN-style Event, Dataselect, Station, and Availability services
when the tables required by each service are configured. Requests for unavailable
services or unsupported detail levels return `503` with the missing table names.

KBWS uses deployment-scoped access control: it does not implement in-app user
authentication or FDSN `queryauth` semantics. For general client compatibility,
The Swagger UI is served at the canonical `/fdsnws` path. KBWS exposes
`/fdsnws/dataselect/1/queryauth` as an alias of the existing `query`
implementation; it is not separately backed and does not provide a second
authorization system. Deploy each instance with appropriately restricted network
visibility, a least-privileged read-only Oracle service identity, and waveform
filesystem mounts matching the data it may serve. Oracle Wallets are an optional
deployment choice; local users may use a normal configured `database_url` against
their own tables.

## Why do this?

With KBWS, you can use any FDSN-WS or rest API client (like ObsPy or [Restish](https://rest.sh)) as the interface with your database, instead of using SQL on a connected server or some other programmatic interface (like Pisces) directly.
Clients like the [ObsPy FDSN Client](https://docs.obspy.org/packages/obspy.clients.fdsn.html), `curl`, or just your web browser become viable ways to acquire data, no home-grown software installations required!

## Installation

### Natively (without containers), using Pixi

Requirements:

* FastAPI
* ObsPY
* SQLAlchemy
* Pisces
* python-dotenv
* The `oracledb` driver for Oracle databases
* Uvicorn (async web server used by FastAPI)

...directly from the repository
```bash
pixi install
pixi shell
```


### Natively using pip and venv

Requirements:

* Python 3.10 or later
* Access to an Oracle database with a CSS-like schema (CSS 3.0 or KB Core)
* Oracle Instant Client for Oracle database connections

For a runtime installation, create and activate a virtual environment, then
install KBWS and its dependencies directly from GitHub:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install "kbws @ git+https://github.com/LANL-Seismoacoustics/kbws.git"
python -m pip install oracledb
```

Pisces is currently installed from its GitHub `main` branch:

```bash
python -m pip install git+https://github.com/LANL-Seismoacoustics/pisces.git@main
```

If `oracledb` cannot auto-detect Oracle Instant Client, set
`oracle_client_lib_dir` in `.env`. See the [configuration](#configuration)
section for the required database and table settings.

### Using Containers/Images

KBWS can also be run from a pre-built container image. See the [Deployment guide](docs/source/deployment.md) for container usage with Docker and Podman.


## Configuration

`kbws` needs to know where your database is and what tables to use, so these are supplied in a small `.env` text file that [python-dotenv](https://saurabh-kumar.com/python-dotenv/) uses to inject variables into your environment at runtime.
KBWS uses these configurations to target FDSN-WS requests to the right database and tables.

Write a file named `.env` like the following:
```
# .env
database_url=oracle://username:password@mydbserver.com:1523/dbname
affiliation=myowner.affiliation
arrival=myowner.arrival
assoc=myowner.assoc
# amplitude=myowner.amplitude  # unused by current KBWS services
# gregion=myowner.gregion  # unused by current KBWS services
# origerr=myowner.origerr  # unused by current KBWS services
# remark=myowner.remark  # unused by current KBWS services
# sregion=myowner.sregion  # unused by current KBWS services
# stamag=myowner.stamag  # unused by current KBWS services
# wftag=myowner.wftag  # unused by current KBWS services
event=myowner.event
instrument=myowner.instrument
netmag=myowner.netmag
network=myowner.network
origin=myowner.origin
sensor=myowner.sensor
site=myowner.site
sitechan=myowner.sitechan
wfdisc=myowner.wfdisc
```


## Access via port forwarding

If you server isn't configured as a web server, you may need to forward the port KBWS is running on to your local machine using an SSH tunnel.
This will allow you to use a server that isn't discoverable as a web server on your network.

For example, if the app is running on port `8000` on `myserver.mydomain.something`, type `ssh -L 8000:localhost:8001 myserver.mydomain.something`.
From your local machine, you can use any FDSN-WS compliant client with a "local" URL, like:

```python
from obspy.clients.fdsn import Client

client = Client('http://localhost:8001', _discover_services=False)
```

The `_discover_services=False` keyword may be necessary if `kbws` doesn't yet serve a proper `application.wadl` file that describes the FDSN endpoints and the services and keywords they offer, which ObsPy expects when initializing its FDSN client.

Remember, the server running KBWS must have the data directories used in the database mounted, with the same directory structure, or else it won't be able to return waveforms.


## Development

Using Pixi:

```bash
git clone https://github.com/LANL-Seismoacoustics/kbws.git
cd kbws
pixi install
pixi shell
```

Using containers: see the [Deployment guide](docs/source/deployment.md) for development with hot reload.

## Command Line Access

The framework that runs KBWS (FastAPI) follows the [OpenAPI specification](https://www.openapis.org/), which means that tools that consume compliant APIs can expect a standardized machine-readable description of the interface.
This means that _any_ tool that can work with OpenAPI compliant interfaces will also work with KBWS.
[Restish](https://rest.sh) is a nice one that can be configured to provide command line flags specific to FDSN Web Services served by KBWS.
After installing, configure your end point (name "kbws" here):

```bash
restish api configure kbws http://some.url.gov:8000
```
...and follow the prompts to answer questions about the API you're configuring.
Then, sync `restish` with the API description, which customizes the command line flags you can use to interact with the endpoint.

```bash
restish api sync kbws
```

Now, you can use `restish` like a custom FDSN-WS CLI.  For example:

```bash
restish kbws event-query --starttime 2012-11-01 --endtime 2012-11-03T01:00:00.00 --minlatitude 40 --maxlatitude 47 --minlongitude -10 --maxlongitude 5 --mindepth 1.3 --maxdepth 100 > quakes.xml
```
...returns your event query as a QuakeML xml file.


## Roadmap

- [ ]  Containerize the whole KBWS web app, starting from [Oracle Linux Instantclient images](https://github.com/oracle/docker-images/blob/main/OracleInstantClient/oraclelinux8/21/Dockerfile).
    - This would allow mounting local database client configurations (e.g. `$ORACLE_HOME/network/admin`) into the container.
    - Follow the FastAPI containerization [docs](https://fastapi.tiangolo.com/deployment/docker/).
- [x] Parameterize the container to allow different core table names
- [ ] Move all injected dependencies (e.g. `get_db`) to a `dependencies.py`, so FastAPI can properly cache them.
- [-] Implement HTTPS that can use containers and .env files, point to .pem/.key/.crt files on host machine.
- [x] Move `Enum` parameters to `Literal[...]` where they enums aren't reused.
- [ ] Move SwaggerUI to `/docs`
- [ ] Serve a static protomaps/pmtiles map page at `/`
- [ ] Plan ahead for versioning by moving endpoints to `api/v1/endpoints`?


## Copyright

O5044 "KBWS: KB Core Web Services"

© 2026. Triad National Security, LLC. All rights reserved.

This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos
National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S.
Department of Energy/National Nuclear Security Administration. All rights in the program are
reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear
Security Administration. The Government is granted for itself and others acting on its behalf a
nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare
derivative works, distribute copies to the public, perform publicly and display publicly, and to permit
others to do so.
