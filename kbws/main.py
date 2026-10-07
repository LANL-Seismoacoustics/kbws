"""
## FDSN Web Services for KB Core databases.

Use common FDSN-WS data access clients to work with local databases.

Read about the [FDSN Web Services specificaton.](https://www.fdsn.org/webservices).

Get *files* using: [ObsPy's Mass Downloader](https://docs.obspy.org/packages/autogen/obspy.clients.fdsn.mass_downloader.html#module-obspy.clients.fdsn.mass_downloader), [Rover](https://earthscope.github.io/rover/), [SOD](http://www.seis.sc.edu/sod/), curl or wget, or your web browser!

Get *live data* using: [ObsPy's FDSN Client](https://docs.obspy.org/packages/obspy.clients.fdsn.html#module-obspy.clients.fdsn), [irisFetch.m for MATLAB](https://github.com/iris-edu/irisFetch-matlab)

**Note:** Not all tools will work out-of-the-box while supporting services are implemented.

### Example: ObsPy FDSN Client

```python
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
client = Client(<IP address>, _discover_services=False)
client.get_waveforms(network='TA', station='A25A', location='--', channel='BH?', starttime=UTCDateTime('2010-03-25T00:00:00'), endtime=UTCDateTime('2010-03-28T00:00:00'))
```

...results in

```python
3 Trace(s) in Stream:
.A25A..BHE | 2010-03-27T23:50:07.000000Z - 2010-03-28T00:00:00.000000Z | 40.0 Hz, 23721 samples
.A25A..BHN | 2010-03-27T23:50:07.000000Z - 2010-03-28T00:00:00.000000Z | 40.0 Hz, 23721 samples
.A25A..BHZ | 2010-03-27T23:50:07.000000Z - 2010-03-28T00:00:00.000000Z | 40.0 Hz, 23721 samples
```

The `_discover_services` keyword allows you to bypass the need for a properly-formatted [WADL](https://en.wikipedia.org/wiki/Web_Application_Description_Language) file for the service, because it's silly that not having this file should cause a request to fail.  I'm just sayin'.

"""
import functools
import io
import logging

from fastapi import FastAPI, Response, Request
from fastapi.routing import APIRoute
from fastapi.responses import PlainTextResponse
from fastapi.exceptions import RequestValidationError
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
import yaml

from . import __version__
from .logging import get_logger
from .routes import availability, dataselect, event, station
from .responses import BadRequestResponse, InternalErrorResponse


SERVICE_VERSIONS = {
        'availability': availability.VERSION,
        'dataselect': dataselect.VERSION,
        'event': event.VERSION,
        'station': station.VERSION,
        'noservice': __version__,
        }

logger = get_logger(__name__)

app = FastAPI(
    title="KB Core FDSNWS",
    description=__doc__,   # TODO: get this from a description.md in the repo
    version=__version__,
    docs_url="/",
    redoc_url=None,  # don't also produce the ReDoc version of the API docs
    contact={
        "name": "Jonathan K MacCarthy",
        "email": "jkmacc@lanl.gov",
    }, # TODO: get these from config.py and .env
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

# attach the dataselect endpoints/routes
app.include_router(availability.router)
app.include_router(dataselect.router)
app.include_router(event.router)
app.include_router(station.router)

# allow requests from any IP:port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# intercept each request to attach the service version to it, so it can be used below
# in validation exceptions (which must be declared globally, not per service)
@app.middleware("http")
async def add_service_version_header(request: Request, call_next):
    if 'station' in request.url.path:
        service = 'station'
    elif 'dataselect' in request.url.path:
        service = 'dataselect'
    elif 'event' in request.url.path:
        service = 'event'
    else:
        service = 'noservice'

    request.state.service_version = SERVICE_VERSIONS.get(service, app.version)
    request = await call_next(request)

    return request

# catch FastAPI's/Starlette's default query parameter validation, and return FDSN-like ones instead.
# XXX: this needs to be specific to the route (...why?) not supported by FastAPI without creating and
# mounting different apps for each service. here, we just give the KBWS version in the message.
# see: https://github.com/tiangolo/fastapi/discussions/8396
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    logger.info("In RequestValidationError handler")
    r = BadRequestResponse(
        content=str(exc),
        service_docs_url=request.base_url,
        submitted_url=str(request.url) + str(request.query_params),
        service_version=getattr(request.state, 'service_version', app.version),
    )
    return r


# @app.exception_handler(ValueError)
@app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
async def internal_error_handler(request: Request, exc):
    logger.error("oops!")
    # r = InternalErrorResponse(
    #     content=str(exc),
    #     service_docs_url=request.base_url,
    #     submitted_url=str(request.url) + str(request.query_params),
    #     service_version=getattr(request.state, 'service_version', app.version),
    # )
    # return r
    return PlainTextResponse("oops response", status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# yaml version of spec, in addition to openapi.json endpoint
@app.get("/openapi.yaml", include_in_schema=False)
@functools.lru_cache()
def read_openapi_yaml():
    openapi_json = app.openapi()
    yaml_s = io.StringIO()
    yaml.dump(openapi_json, yaml_s)
    return Response(yaml_s.getvalue(), media_type="text/yaml")


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function names.

    Note: Should be called only after all routes have been added.

    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name  # in this case, 'read_items'

use_route_names_as_operation_ids(app)
