# Usage

KBWS exposes FDSN Web Services over HTTP. Command-line tools, Python clients,
and other FDSN-compatible applications can query events and waveforms from a
running KBWS instance.

The examples below assume the service is available at
`http://localhost:8000`.

## Using ObsPy

Use ObsPy's FDSN client for event and waveform queries. Set
`_discover_services=False` because KBWS does not provide all of the service
discovery metadata expected by ObsPy.

```python
from obspy.clients.fdsn import Client

client = Client("http://localhost:8000", _discover_services=False)

catalog = client.get_events(
    starttime="2012-11-01",
    endtime="2012-11-03",
    minlatitude=40,
    maxlatitude=47,
)

stream = client.get_waveforms(
    network="IU",
    station="ANMO",
    location="00",
    channel="BH?",
    starttime="2012-11-01T00:00:00",
    endtime="2012-11-01T01:00:00",
)
```

For a deployment protected by HTTP Digest authentication, pass the deployment
credentials to the ObsPy client:

```python
from obspy.clients.fdsn import Client

client = Client(
    "https://data.example.org",
    user="USERNAME",
    password="PASSWORD",
    _discover_services=False,
)
```

## ObsPy and local certificate stores

When a deployment certificate is trusted by the operating system but not by
Python's default CA bundle, ObsPy clients may need the `truststore` package.
This can occur with macOS system keychains. Inject the system trust store before
importing or using ObsPy:

```python
import truststore
truststore.inject_into_ssl()

from obspy.clients.fdsn import Client
```

Install `truststore` in the same environment as ObsPy. This is preferable to
disabling TLS certificate verification. A deployment may instead provide its CA
bundle through the normal Python/OpenSSL configuration.

## Using curl

KBWS endpoints can also be queried directly with `curl`:

```bash
# Get events as QuakeML
curl "http://localhost:8000/fdsnws/event/1/query?starttime=2012-11-01&endtime=2012-11-03&minlatitude=40&maxlatitude=47"

# Get waveforms as MiniSEED
curl "http://localhost:8000/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2012-11-01T00:00:00&end=2012-11-01T01:00:00" -o data.mseed
```

For HTTP Digest authentication, use curl's `--digest` option and credentials
from the deployment:

```bash
curl --digest -u 'USERNAME:PASSWORD' \\
  "https://data.example.org/fdsnws/event/1/query?starttime=2012-11-01" \\
  -o events.xml
```

## Using Restish

[Restish](https://rest.sh) can consume the KBWS OpenAPI description and provide
an FDSN-oriented command-line interface. After installing Restish, configure
and synchronize an endpoint:

```bash
restish api configure kbws http://localhost:8000
restish api sync kbws
```

For a Digest-protected deployment, provide the credentials when invoking
Restish (or configure them using the equivalent Restish authentication prompt):

```bash
restish --auth 'USERNAME:PASSWORD' kbws event-query --starttime 2012-11-01
```

For example, query events and save the QuakeML response:

```bash
restish kbws event-query \
  --starttime 2012-11-01 \
  --endtime 2012-11-03T01:00:00.00 \
  --minlatitude 40 \
  --maxlatitude 47 \
  --minlongitude -10 \
  --maxlongitude 5 \
  --mindepth 1.3 \
  --maxdepth 100 > quakes.xml
```

## Access through an SSH tunnel

If the server is not directly reachable as a web server, forward its KBWS
port to your local machine with SSH. For example, if KBWS listens on port
`8000` on `myserver.example.org`:

```bash
ssh -L 8000:localhost:8000 myserver.example.org
```

Then use `http://localhost:8000` with `curl`, Restish, or ObsPy. The server
must also have the waveform directories mounted at the same paths recorded in
its database; otherwise waveform queries can succeed while waveform reads
fail.
