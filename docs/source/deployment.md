# Deployment

This guide covers deployment of KBWS as a native service and as an optional
rootless Podman service. The container workflow is intended for a Linux host
with Podman configured for the account that runs the service.

## Native Deployment

### Running KBWS

Start KBWS using uvicorn:

```bash
# Development mode with auto-reload
python -m kbws

# Single-process service
uvicorn kbws.main:app --host 0.0.0.0 --port 8000
```

Scaling with multiple workers is intentionally outside the scope of this
deployment guide. If it is needed later, measure database connection usage,
latency, and memory before selecting a process or replica strategy.

### Running as a user systemd Service

A native installation can be managed by the invoking user's systemd instance.
Create `~/.config/systemd/user/kbws.service`:

```ini
[Unit]
Description=KBWS FDSN Web Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/kbws
Environment=PATH=%h/.venv/bin:/usr/local/bin:/usr/bin
Environment=PYTHONUNBUFFERED=1
ExecStart=%h/.venv/bin/uvicorn kbws.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Adjust `WorkingDirectory`, `PATH`, and `ExecStart` to match the native
installation. The `EnvironmentFile` mechanism may be used if the service's
runtime environment file is stored separately and is readable by the user.
Do not put credentials directly in the unit file.

Enable and start the user service:

```bash
systemctl --user daemon-reload
systemctl --user enable --now kbws.service
systemctl --user status kbws.service
```

To keep user services running after logout, enable lingering for the account
if permitted by the host:

```bash
loginctl enable-linger
```

## Podman Deployment

The repository includes `Containerfile` and
`podman-compose.yml` for an optional Podman-based deployment. The image starts
from Python 3.13, installs KBWS with pip, runs one Uvicorn process, and does
not require Pixi at runtime. Pixi remains useful for development and testing.

The compose file is deliberately deployment-neutral. It expects container
launch settings to be supplied by the Compose project `.env` file or the
invoking shell, while the application settings remain in a separate runtime
environment file mounted at `/app/.env`. It does not publish a database port;
KBWS makes outbound database connections.

### Prerequisites

- A Linux host with rootless Podman and `podman-compose` configured.
- Access to the Python base image while building the image.
- A runtime `.env` file containing the required KBWS database and table
  settings. Keep this file outside version control.
- Read access to every data directory referenced by the database.
- A writable, persistent host directory for logs.

The container uses the invoking user's numeric UID and GID. This is important
for rootless Podman and for NFS-backed data: the NFS server and host kernel
check numeric ownership and supplementary groups. The compose file requests
`userns_mode: keep-id` and `group_add: keep-groups`; the latter depends on the
host's rootless Podman configuration.

### Simple deployment

For a single data tree, create a local, untracked Compose project `.env`
next to `podman-compose.yml`:

```dotenv
KBWS_UID=1000
KBWS_GID=1000
KBWS_ENV_FILE=/path/to/kbws.env
KBWS_LOG_DIR=/path/to/persistent/kbws-logs
KBWS_DATA_DIR=/path/to/data/tree
KBWS_HTTP_PORT=8000
```

The separate `/path/to/kbws.env` file contains only KBWS application settings
and secrets. Prepare the persistent log directory, then start the service:

```bash
mkdir -p /path/to/persistent/kbws-logs
podman-compose -f podman-compose.yml up --build -d
```

For a convenient local launch without editing the Compose `.env`, shell
variables override its values:

```bash
KBWS_UID=$(id -u) \\
KBWS_GID=$(id -g) \\
KBWS_LOG_DIR="$PWD/test-logs" \\
KBWS_DATA_DIR="$PWD/test-data" \\
podman-compose -f podman-compose.yml up --build -d
```

The important path rule is that `KBWS_DATA_DIR` is mounted at the **same path
inside the container** as on the host. For example, a value of
`/path/to/data/tree` produces this bind mount:

```text
/path/to/data/tree:/path/to/data/tree:ro
```

This is required because KBWS reads waveform `dir` and `dfile` values directly
from the database. The compose file does not provide a data-path remapping
option. The data tree is read-only; the log directory is writable and
persistent.

Useful compose settings include:

- `KBWS_HTTP_PORT`: host port published to container port 8000; defaults to
  `8000`.
- `KBWS_ENV_FILE`: host path to the separate application settings file.
- `KBWS_LOG_DIR`: host path for persistent logs; defaults to `./logs`.
- `KBWS_DATA_DIR`: required host data path, also used as the container path.
The application `log_level` setting belongs in the separate application
settings file; the compose file selects the server logging configuration.

The compose health check requests
`/fdsnws/event/1/version` from inside the container. Check status and logs with:

```bash
podman-compose -f podman-compose.yml ps
podman logs <container-name>
curl http://127.0.0.1:8000/fdsnws/event/1/version
```

Stop the service with:

```bash
podman-compose -f podman-compose.yml down
```

### Running the Podman service with user systemd

The compose workflow is useful for building and checking the service. For
long-running rootless Podman deployments, a user-level systemd unit or a
Quadlet is usually preferable because systemd can start the service after
login (or with lingering enabled), restart it, and collect its status.

#### User-level systemd unit using podman-compose

Create `~/.config/systemd/user/kbws-compose.service`:

```ini
[Unit]
Description=KBWS Podman Compose service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=%h/kbws
Environment=KBWS_UID=%U
Environment=KBWS_GID=%G
Environment=KBWS_ENV_FILE=%h/.config/kbws/kbws.env
Environment=KBWS_LOG_DIR=%h/.local/state/kbws/logs
Environment=KBWS_DATA_DIR=/path/to/data/tree
ExecStart=/usr/bin/podman-compose -f %h/kbws/podman-compose.yml up --build -d
ExecStop=/usr/bin/podman-compose -f %h/kbws/podman-compose.yml down

[Install]
WantedBy=default.target
```

The unit runs as the invoking user; it does not use `sudo` or a system-wide
unit. Adjust only the generic repository and data paths for the local
installation. Enable it with:

```bash
systemctl --user daemon-reload
systemctl --user enable --now kbws-compose.service
systemctl --user status kbws-compose.service
```

Because the unit is `Type=oneshot` with `RemainAfterExit=yes`, systemd tracks
the compose operation rather than the Uvicorn process directly. Podman and the
compose tool remain responsible for the container lifecycle. A Quadlet gives
systemd direct ownership of that lifecycle and is generally the better
long-term option.

#### Quadlet

Quadlet files are placed in `~/.config/containers/systemd/` for rootless
Podman. A simple `kbws.container` can build the image using Podman's normal
build command and then run it:

```ini
[Unit]
Description=KBWS Podman container

[Container]
Image=localhost/kbws:latest
PublishPort=8000:8000
Environment=LOG_LEVEL=INFO
Environment=LOGGING_CONFIG=logging.server.ini
User=%U:%G
UserNS=keep-id
GroupAdd=keep-groups
Volume=%h/.config/kbws/kbws.env:/app/.env:ro
Volume=%h/.local/state/kbws/logs:/var/log/kbws:rw
Volume=/path/to/data/tree:/path/to/data/tree:ro
Exec=sh -c "umask 0002 && exec python -m uvicorn kbws.main:app --host 0.0.0.0 --port 8000"

[Service]
Restart=unless-stopped

[Install]
WantedBy=default.target
```

Build the image before enabling the Quadlet:

```bash
podman build -f Containerfile -t localhost/kbws:latest .
mkdir -p ~/.local/state/kbws/logs
systemctl --user daemon-reload
systemctl --user enable --now kbws.service
systemctl --user status kbws.service
```

The Quadlet example uses the same identity, read-only data, writable log,
and single-process settings as `podman-compose.yml`. The data source and
container target must be identical. If absolute symbolic links refer to other
data trees, add one identical-path `Volume=` line for each target tree.
Quadlet syntax and supported options depend on the installed Podman version;
check `podman-systemd.unit(5)` if an option is rejected.

### Multiple data trees and absolute symlinks

If the primary data tree contains absolute symbolic links whose targets are in
other trees, every target tree must also be mounted read-only at its original
absolute path. Relative links within a mounted tree normally continue to work
without additional configuration.

The base compose file handles one required data tree. Add further trees in a
local, untracked compose override. For example, `data-mounts.override.yml`
may contain:

```yaml
services:
  kbws:
    volumes:
      - type: bind
        source: /path/to/linked/tree/one
        target: /path/to/linked/tree/one
        read_only: true
      - type: bind
        source: /path/to/linked/tree/two
        target: /path/to/linked/tree/two
        read_only: true
```

The source and target of each mount must be identical. This preserves the
absolute paths stored in database records and used by symbolic links. Keep the
override file out of version control if it contains site-specific paths.

Start with both compose files:

```bash
KBWS_UID=$(id -u) \\
KBWS_GID=$(id -g) \\
KBWS_LOG_DIR="$PWD/test-logs" \\
KBWS_DATA_DIR="$PWD/test-data" \\
podman-compose \\
  -f podman-compose.yml \\
  -f data-mounts.override.yml \\
  up --build -d
```

### Podman and file permissions

`--group-add=keep-groups` is represented by `group_add: keep-groups` in the
compose file. It asks rootless Podman to retain the invoking user's
supplementary groups, which may be necessary for NFS and shared-group access.
It is not a substitute for correct permissions on the host or at the NFS
server.

The compose command sets a `0002` umask so files created in the writable log
mount are group-readable and group-writable when the directory permissions
allow it. A setgid log directory can be used when log files should inherit a
shared group:

```bash
install -d -m 2775 /path/to/persistent/kbws-logs
```

Verify the effective identity and mounts after startup:

```bash
podman exec <container-name> id
podman exec <container-name> findmnt
ls -ln /path/to/persistent/kbws-logs
```

Files written to bind mounts have numeric ownership determined by the
container's rootless identity mapping. Using `keep-id` and the invoking user's
UID/GID makes host-side ownership correspond to that user. The container does
not persist HTTP response bodies as files; the persistent application artifact
in this setup is the rotating log file.

### Configuration requirements

KBWS requires a separate application settings file in the container at
`/app/.env`. Set `KBWS_ENV_FILE` in the Compose project `.env` (or the shell)
to its host path; the compose file mounts that file read-only. Container launch
settings such as `KBWS_UID`, `KBWS_GID`, `KBWS_LOG_DIR`, and `KBWS_DATA_DIR` do
not belong in the application settings file. Do not bake credentials or other
deployment secrets into the image.

The image uses `logging.server.ini`, which writes rotating logs to
`/var/log/kbws/kbws.log`. That directory is supplied by the writable host log
mount.

### Troubleshooting

#### Container cannot read waveform files

- Confirm that every database `dir`/`dfile` path exists at the identical path
  inside the container.
- Mount absolute symbolic-link targets at their identical paths as well.
- Verify the invoking user's UID and supplementary groups with `podman exec
  <container-name> id`.
- Confirm NFS server-side permissions and rootless Podman group retention.
- Confirm each data bind mount is read-only and present with `podman inspect`.

#### Container cannot read `.env`

Ensure the host environment file is readable by the invoking user and that
`KBWS_ENV_FILE` points to the correct file. It is mounted read-only at
`/app/.env`.

#### Logs are missing or not writable

Ensure `KBWS_LOG_DIR` exists and is writable by the invoking user. Inspect the
container logs and the host directory permissions. The application log file is
`/var/log/kbws/kbws.log` inside the container.

#### Database connection failures

Check the database URL and table mappings in the runtime `.env`, confirm that
the container host can reach the database, and review the application logs.
No database listener needs to be published by the container.
