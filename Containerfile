# Deployment image for the KBWS FastAPI service.
# This file is intentionally separate from the general package: it is a
# deployment artifact, not a package default.
FROM python:3.13-bookworm

# Oracle Instant Client is installed at a stable path for thick-mode
# oracledb connections. The package is downloaded from Oracle's public CDN;
# override ORACLE_IC_DIR/ORACLE_IC_URL in a deployment-specific build if
# a different approved client release is required.
ARG ORACLE_IC_DIR=instantclient_23_5
ARG ORACLE_IC_URL=https://download.oracle.com/otn_software/linux/instantclient/235000/instantclient-basic-linux.x64-23.5.0.24.07.zip

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates curl unzip libaio1 \
    && mkdir -p /opt/oracle \
    && curl -fL --retry 3 "$ORACLE_IC_URL" -o /tmp/instantclient.zip \
    && unzip -q /tmp/instantclient.zip -d /opt/oracle \
    && ln -s "/opt/oracle/${ORACLE_IC_DIR}" /opt/oracle/instantclient \
    && rm /tmp/instantclient.zip \
    && rm -rf /var/lib/apt/lists/*

ENV ORACLE_CLIENT_LIB_DIR=/opt/oracle/instantclient \
    LD_LIBRARY_PATH=/opt/oracle/instantclient \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    TNS_ADMIN=/opt/oracle/network/admin

WORKDIR /app

# Install the package and its Oracle-capable dependency set. This image is
# deliberately simple rather than minimized; the full Debian Python image
# avoids native-library surprises for ObsPy and database drivers.
COPY pyproject.toml README.md LICENSE.txt ./
COPY kbws ./kbws
RUN python -m pip install --upgrade pip \
    && python -m pip install ".[oracle]"

COPY logging.dev.ini logging.server.ini ./

# The database configuration is supplied at runtime as /app/.env. Do not
# bake credentials or deployment database settings into this image. Runtime
# ownership, group membership, logging, and umask are deployment decisions.
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin kbws \
    && chown -R kbws:kbws /app \
    && chmod -R a+rX /app
USER kbws

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "kbws.main:app", "--host", "0.0.0.0", "--port", "8000"]
