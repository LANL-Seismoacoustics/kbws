# KBWS: FDSN Web Services for CSS-like SQL Databases

Have a CSS-like SQL database (CSS 3.0, KB Core), and wish it had an [FDSN Web Services](https://www.fdsn.org/webservices/) endpoint?
This package uses [FastAPI](https://fastapi.tiangolo.com/) and [Pisces](https://github.com/LANL-Seismoacoustics/pisces) to provide a FDSN-WS on your CSS database.

## Why do this?

With KBWS, you can use any FDSN-WS or rest API client (like ObsPy or [Restish](https://rest.sh)) as the interface with your database, instead of using SQL on a connected server or some other programmatic interface (like Pisces) directly.
Clients like the [ObsPy FDSN Client](https://docs.obspy.org/packages/obspy.clients.fdsn.html), `curl`, or just your web browser become viable ways to acquire data, no home-grown software installations required!

## Installation

### Natively (without containers), using Conda

Requirements:

* FastAPI
* ObsPY
* SQLAlchemy
* Pisces
* python-dotenv
* A database driver, like `cx_Oracle` or `oracledb` for Oracle databases
* Uvicorn (async web server used by FastAPI)

...directly from the repository
```bash
conda env create -f environment.yml
conda activate kbws
pip install git+https://github.com/LANL-Seismoacoustics.git
```


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
amplitude=myowner.amplitude
arrival=myowner.arrival
assoc=myowner.assoc
event=myowner.event
gregion=myowner.gregion
instrument=myowner.instrument
lastid=myowner.lastid
netmag=myowner.netmag
network=myowner.network
origerr=myowner.origerr
origin=myowner.origin
remark=myowner.remark
sensor=myowner.sensor
site=myowner.site
sitechan=myowner.sitechan
sregion=myowner.sregion
stamag=myowner.stamag
wfdisc=myowner.wfdisc
wftag=myowner.wftag
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

Using conda:

```bash
git clone https://github.com/LANL-Seismoacoustics/kbws.git
cd kbws
pip install -e .
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
- [ ] Add unified logging, possibly employing FastAPI background tasks so it doesn't add to response times.
- [ ] Move all injected dependencies (e.g. `get_db`) to a `dependencies.py`, so FastAPI can properly cache them.
- [ ] Implement HTTPS that can use containers and .env files, point to .pem/.key/.crt files on host machine.
- [ ] Move `Enum` parameters to `Literal[...]` where they enums aren't reused.
- [ ] Implement OAuth or JWT token authentication that checks for username in database, initialize db session
- [ ] Move SwaggerUI to `/docs`
- [ ] Serve a static protomaps/pmtiles map page at `/`
- [ ] Plan ahead for versioning by moving endpoints to `api/v1/endpoints`?
