# Installation

KBWS can be installed natively using Pixi or pip. Podman deployment is documented separately in the [Deployment guide](deployment.md).

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

### Offline installation with pixi-pack

See the [`pixi-pack` documentation](https://prefix-dev.github.io/pixi-pack/) for
additional packaging options. Use `pixi-pack` to prepare a complete,
self-extracting environment on a machine
with network access, then move the resulting shell script to the offline host.
Build it for the target operating system and architecture; for example, build a
Linux environment from a Linux machine (or a matching Pixi host):

```bash
pixi-pack \
  --environment default \
  --platform linux-64 \
  --create-executable \
  --output-file kbws-environment.sh
```

Copy `kbws-environment.sh` and the KBWS source/configuration to the offline
host. Make the environment script executable and run it from a directory where
it is allowed to create temporary files:

```bash
chmod +x kbws-environment.sh
./kbws-environment.sh
```

The executable extracts the packed environment and prints the activation
instructions. If execution from `/tmp` is restricted, choose a writable
temporary directory before running it:

```bash
mkdir -p "$HOME/.tmp"
export TMPDIR="$HOME/.tmp"
./kbws-environment.sh
```

Activate the extracted environment with `conda` on the offline host. Use the
extraction path printed by `pixi-pack`:

```bash
conda activate /path/to/extracted/environment
```

If the host has no `conda` shell function yet, initialize it once for the
current shell before activating:

```bash
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate /path/to/extracted/environment
```

Then run KBWS normally from the source directory:

```bash
python -m kbws
```

The packed environment is platform-specific and includes package artifacts;
rebuild it when `pixi.lock` or the target platform changes. Keep the runtime
`.env` file separate and copy it to the working directory on the offline host.

### Using pip

If you prefer to use pip directly:

```bash
pip install fastapi uvicorn obspy sqlalchemy pydantic-settings python-dotenv
pip install oracledb
pip install git+https://github.com/LANL-Seismoacoustics/pisces.git@main
pip install -e .
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
arrival=schema.arrival
assoc=schema.assoc
# amplitude=schema.amplitude  # unused by current KBWS services
# gregion=schema.gregion  # unused by current KBWS services
# origerr=schema.origerr  # unused by current KBWS services
# remark=schema.remark  # unused by current KBWS services
# sregion=schema.sregion  # unused by current KBWS services
# stamag=schema.stamag  # unused by current KBWS services
# wftag=schema.wftag  # unused by current KBWS services
event=schema.event
instrument=schema.instrument
netmag=schema.netmag
network=schema.network
origin=schema.origin
sensor=schema.sensor
site=schema.site
sitechan=schema.sitechan
wfdisc=schema.wfdisc_raw
```

### Oracle Client Configuration

The package uses `oracledb` for Oracle connections. If thick mode is required
and the client is not auto-detected, set `oracle_client_lib_dir` in `.env`
and install Oracle Instant Client from [Oracle's website](https://www.oracle.com/database/technologies/instant-client.html).

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

**Solution:** Install Pisces from the GitHub `main` branch:
```bash
pip install git+https://github.com/LANL-Seismoacoustics/pisces.git@main
```