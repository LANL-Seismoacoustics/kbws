# Installation

KBWS can be installed natively using Conda/pip or run in containers using Docker or Podman.

## Prerequisites

* Python 3.10 or later
* Access to an Oracle database with CSS-like schema (CSS 3.0 or KB Core)
* Oracle Instant Client (for Oracle database connections)

## Native Installation

### Using pixi (Recommended for Development)

```bash
git clone https://github.com/LANL-seismoacoustics/kbws.git
cd kbws
pixi install
pixi shell
```

This will create the base environment with all runtime dependencies. For development with testing and documentation tools:

```bash
pixi shell -e dev
```

### Using Conda

#### Production Environment

```bash
git clone https://github.com/LANL-seismoacoustics/kbws.git
cd kbws
conda env create -f environment.yml
conda activate kbws
pip install -e .
```

#### Development Environment

```bash
conda env create -f environment-dev.yml
conda activate kbws-dev
pip install -e .
```

The development environment includes additional packages for testing (`pytest`, `httpx`) and uses `oracledb` instead of `cx_oracle` for better MacOS compatibility.

### Using pip

If you prefer to use pip directly:

```bash
pip install fastapi uvicorn obspy sqlalchemy pydantic-settings python-dotenv
pip install oracledb  # or cx_oracle for Linux
pip install git+https://github.com/LANL-Seismoacoustics/pisces.git
pip install -e .
```

## Container Installation

KBWS can be run from pre-built container images using Docker or Podman.

### Using Docker

```bash
docker pull ghcr.io/lanl-seismoacoustics/kbws:latest
```

### Using Podman

```bash
podman pull ghcr.io/lanl-seismoacoustics/kbws:latest
```

## Configuration

KBWS requires a `.env` file to configure database connections and table mappings. Create a file named `.env` in your working directory:

```bash
# Database connection
database_url=oracle://username:password@hostname:1523/database

# Logging
log_level=INFO

# Optional: Oracle Instant Client library directory
# Only needed if oracledb cannot auto-detect the client
# oracle_client_lib_dir=/opt/oracle/instantclient_23_3

# Table mappings (adjust schema.table names for your database)
affiliation=schema.affiliation
amplitude=schema.amplitude
arrival=schema.arrival
assoc=schema.assoc
event=schema.event
gregion=schema.gregion
instrument=schema.instrument
lastid=schema.lastid
netmag=schema.netmag
network=schema.network
origerr=schema.origerr
origin=schema.origin
remark=schema.remark
sensor=schema.sensor
site=schema.site
sitechan=schema.sitechan
sregion=schema.sregion
stamag=schema.stamag
wfdisc=schema.wfdisc_raw
wftag=schema.wftag
```

### Oracle Client Configuration

KBWS supports both `oracledb` (recommended for development/MacOS) and `cx_oracle` (recommended for production/Linux):

**Development (oracledb):**
- If Oracle Instant Client is not auto-detected, set `oracle_client_lib_dir` in `.env`
- Download Oracle Instant Client from [Oracle's website](https://www.oracle.com/database/technologies/instant-client.html)

**Production (cx_oracle):**
- The Conda environment includes `oracle-instantclient` package
- No additional configuration typically needed

## Verifying Installation

Start the KBWS service:

```bash
# Direct Python (dev mode with hot reload)
python -m kbws

# Via uvicorn (more control)
uvicorn kbws.main:app --host 0.0.0.0 --port 8000 --reload
```

Then test the service:

```bash
# Check service version
curl http://localhost:8000/fdsnws/event/1/version

# Query application.wadl
curl http://localhost:8000/fdsnws/event/1/application.wadl
```

If these commands return valid responses, your installation is working correctly.

## Troubleshooting

### Service won't start

**Problem:** `FileNotFoundError` or configuration errors on startup

**Solution:** Ensure `.env` file exists in the working directory with all required variables

### Oracle client not found

**Problem:** `DPI-1047: Cannot locate a 64-bit Oracle Client library` or similar errors

**Solution:** 
1. Install Oracle Instant Client
2. Set `oracle_client_lib_dir` in `.env` pointing to the client directory
3. On Linux, you may need to run `ldconfig` or set `LD_LIBRARY_PATH`

### Import errors for Pisces

**Problem:** `ModuleNotFoundError: No module named 'pisces'`

**Solution:** Pisces is not available on PyPI. Install it directly from GitHub:
```bash
pip install git+https://github.com/LANL-Seismoacoustics/pisces.git
```

### Container permission issues

**Problem:** Container cannot read waveform files or `.env` file

**Solution:** 
- For Podman: Use `--group-add=keep-groups` flag
- Ensure mounted paths match exactly what's in the database `wfdisc` table
- Check file permissions on host system
