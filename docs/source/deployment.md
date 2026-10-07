# Deployment

This guide covers KBWS-specific deployment configurations, including native service setup and container deployments.

## Native Deployment

### Running KBWS

Start KBWS using uvicorn:

```bash
# Development mode with auto-reload
python -m kbws

# Production mode with multiple workers
uvicorn kbws.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The number of workers should generally be `(2 x num_cores) + 1`.

### Running as a systemd Service

Example systemd service file `/etc/systemd/system/kbws.service`:

```ini
[Unit]
Description=KBWS FDSN Web Service
After=network.target

[Service]
Type=simple
User=kbws
WorkingDirectory=/opt/kbws
Environment="PATH=/opt/conda/envs/kbws/bin"
ExecStart=/opt/conda/envs/kbws/bin/uvicorn kbws.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable kbws
sudo systemctl start kbws
sudo systemctl status kbws
```

## Container Deployment (under construction)

### Docker

**Basic deployment:**

```bash
docker run -d \
  --name kbws \
  -v /path/to/.env:/tmp/.env:ro \
  -v /path/to/waveforms:/path/to/waveforms:ro \
  -p 8000:8000 \
  -p 1523:1523 \
  ghcr.io/lanl-seismoacoustics/kbws:latest
```

**With docker-compose:**

```yaml
version: '3.8'

services:
  kbws:
    image: ghcr.io/lanl-seismoacoustics/kbws:latest
    container_name: kbws
    ports:
      - "8000:8000"
      - "1523:1523"
    volumes:
      - ./env:/tmp/.env:ro
      - /sa:/sa:ro
      - /g:/g:ro
    restart: unless-stopped
    environment:
      - LOG_LEVEL=INFO
```

Start the service:

```bash
docker-compose up -d
```

### Podman (Rootless)

Rootless Podman requires the `--group-add=keep-groups` flag to retain read access to mounted directories:

```bash
podman run -d \
  --name kbws \
  --group-add=keep-groups \
  -v /path/to/.env:/tmp/.env:ro \
  -v /path/to/waveforms:/path/to/waveforms:ro \
  -p 8000:8000 \
  -p 1523:1523 \
  ghcr.io/lanl-seismoacoustics/kbws:latest
```

### Development with Hot Reload

For development with live code reloading:

```yaml
version: '3.8'

services:
  kbws-dev:
    build: .
    container_name: kbws-dev
    ports:
      - "8000:8000"
      - "1523:1523"
    volumes:
      - .:/tmp
      - /sa:/sa:ro
      - /g:/g:ro
    command: uvicorn kbws.main:app --host 0.0.0.0 --port 8000 --reload
```

## KBWS Configuration Requirements

### Environment File (Mandatory)

KBWS requires a `.env` file in its working directory. The service will not start without it. See the [Installation](installation.md) guide for a complete example.

### Waveform Directory Paths (Critical for dataselect)

For the `dataselect` service to retrieve waveforms:

1. Waveform directories must be accessible at **identical paths** as stored in the database
2. Container mounts must exactly match `wfdisc.dir` paths
3. All symlinked directories must also be mounted with matching paths

**Example:** If `wfdisc.dir` contains `/sa/archive/2012/001/`, you must mount:

```bash
-v /sa:/sa:ro
```

**Not** `-v /sa:/data` or any other path mapping, since KBWS reads paths directly from the database.

## SSH Port Forwarding for Remote Access

If your KBWS server is not publicly accessible, use SSH port forwarding:

```bash
# Forward remote port 8000 to local port 8000
ssh -L 8000:localhost:8000 user@server.example.com
```

Then access KBWS from your local machine:

```python
from obspy.clients.fdsn import Client

client = Client('http://localhost:8000', _discover_services=False)
```

**Note:** The `_discover_services=False` flag is required if KBWS doesn't serve a complete `application.wadl` file.

## Monitoring KBWS

### Service Health Checks

KBWS exposes version endpoints for monitoring:

- `/fdsnws/event/1/version` - Event service version
- `/fdsnws/station/1/version` - Station service version
- `/fdsnws/dataselect/1/version` - Dataselect service version
- `/docs` - Interactive API documentation (Swagger UI)

### Container Health Check

Example docker-compose health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/fdsnws/event/1/version"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

### Container Resource Limits

Limit container resources:

```bash
docker run -d \
  --name kbws \
  --memory="2g" \
  --cpus="2.0" \
  # ... other options
```

## Logging

### Log Configuration

Set log level in `.env`:

```bash
log_level=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

Logs are written to `/tmp/logs` inside the container. Mount this directory to persist logs:

```bash
-v /var/log/kbws:/tmp/logs
```

## Security Notes

1. **Database Credentials**: Never commit `.env` files to version control
2. **Read-Only Mounts**: Mount waveform directories as read-only (`:ro`) when possible
3. **Container User**: KBWS container runs as non-root user in `/tmp`

## Troubleshooting

### Container cannot access database

**Problem:** Connection refused or timeout errors

**Solution:**
- Ensure database port (e.g., 1523) is exposed/accessible from container
- Verify database credentials in `.env`
- For Docker: try `--network=host` if network isolation is causing issues

### Waveform files not found

**Problem:** Service returns 204 No Content for valid waveform queries

**Solution:**
- Verify waveform directories are mounted with **exact** paths from `wfdisc` table
- Check file permissions - container user must have read access
- For Podman: ensure `--group-add=keep-groups` is set
- Test file access: `podman exec kbws ls /path/to/waveforms`

### Service won't start

**Problem:** Container exits immediately or service fails to start

**Solution:**
- Verify `.env` file is mounted at `/tmp/.env`
- Check `.env` contains all required variables (see [Installation](installation.md))
- Review logs: `docker logs kbws` or `podman logs kbws`
