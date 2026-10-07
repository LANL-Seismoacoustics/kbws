"""
Functions that translate parsed HTTP event request arguements from FastAPI to
database queries, and return Stream objects and HTTP responses.

We also define the dataselect query paremeters via a Pydantic Model, with
appropriate descriptions.

"""
# Declare models/fields used in this service
# see https://www.fdsn.org/webservices/fdsnws-dataselect-1.1.pdf
# https://fastapi.tiangolo.com/tutorial/dependencies/classes-as-dependencies/?h=depends#type-annotation-vs-depends
# https://fastapi.tiangolo.com/tutorial/query-params-str-validations/?h=query%28#make-it-required

from datetime import datetime
from functools import lru_cache, reduce
from typing import Annotated

from pydantic import ValidationError
from fastapi import APIRouter, Response, Depends, Query, Request, Body
from fastapi.responses import PlainTextResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from obspy import UTCDateTime

# from pisces import request
from pisces.fdsn import Client
from pisces.util import _get_entities

from ..logging import get_logger
from .. import database as db
from ..responses import FDSNErrorText, BAD_REQUEST, NO_DATA, BadRequestResponse
from ..models import DataselectQuery
from ..formats import WAVEFORM_FORMATS, post_parse

VERSION = "1.1.0"
MAJOR_VERSION = VERSION.split(".")[0]

# file name template for file responses
# current_time needed to avoid overwriting
FILENAME_FMT = "fdsn-dataselect_{current_time}.{file_extension}"

logger = get_logger(__name__)

# TODO: add this to package data during installation
#@lru_cache
def get_wadl():
    """Return the WADL text, but cache it, so subsequent calls don't hit the disk."""
    with open("kbws-dataselect.xml", "r") as wadl_file:
        return wadl_file.read()


# All subsequent routes originate at this path
router = APIRouter(prefix=f"/fdsnws/dataselect/{MAJOR_VERSION}", tags=['dataselect'])


@router.get("/application.wadl", summary="Download the service WADL file")
def dataselect_wadl(wadl: str = Depends(get_wadl)):
    return Response(content=wadl, media_type="application/xml")


@router.get("/version", response_class=PlainTextResponse, summary="Return the service version.")
def dataselect_version():
    return VERSION

# Testing HTTP Digest from https://fastapi.tiangolo.com/reference/security/#fastapi.security.HTTPDigest--example
from fastapi.security import HTTPAuthorizationCredentials, HTTPDigest
security = HTTPDigest()
@router.get("/queryauth1", summary="Experimental HTTP Digest Auth endpoint, test 1.")
def dataselect_queryauth1(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
):
    """ works with: curl -L  "http://0.0.0.0:8000/fdsnws/dataselect/1/queryauth/"  -H 'Authorization: Digest myt0ken' """
    logger.warning(credentials.scheme, credentials.credentials)
    return {"scheme": credentials.scheme, "credentials": credentials.credentials}

# HTTP digest attempt 2, from https://stackoverflow.com/a/70268255/745557
from fastapi import Security
http_digest = HTTPDigest()
def authorize_digest(credentials: HTTPAuthorizationCredentials = Security(http_digest)):
    print(credentials.scheme, credentials.credentials)
    # TODO: make this depend on db.get_db?


@router.get("/queryauth2", dependencies=[Depends(authorize_digest)], summary="Experimental HTTP Digest Auth endpoint test 2.")
def dataselect_queryauth2():
    return {"success": "true"}

# attempt to make an actual /queryauth
# think of a way to chain dependencies on authorize_digest, db.get_db Session, etc...
# https://fastapi.tiangolo.com/advanced/advanced-dependencies/#use-cases-with-early-exit-code
@router.get("/queryauth", dependencies=[Depends(authorize_digest)], summary="HTTP Digest Authenticated query endpoint")
def dataselect_queryauth(
    params: Annotated[DataselectQuery, Query()],
    session: Session = Depends(db.get_db)
):
    print(params.model_dump())

    return "looks good!"


@router.get("/query", summary="Download data using URL query parameters")
def dataselect_query(
    params: Annotated[DataselectQuery, Query()],
    session: Session = Depends(db.get_db)
):
    """Query URL builder

    ### Example

    [http://0.0.0.0:8000/fdsnws/dataselect/1/query?channel=BH?&endtime=2010-03-28&format=miniseed&location=--&network=TA&starttime=2010-03-25&station=A25A](http://0.0.0.0:8000/fdsnws/dataselect/1/query?channel=BH?&endtime=2010-03-28&format=miniseed&location=--&network=TA&starttime=2010-03-25&station=A25A)

    """

    # print(params.model_dump())

    client = Client(session,
        affiliation=db.Affiliation,
        wfdisc=db.Wfdisc,
    )

    out = client.get_waveforms(
        starttime=UTCDateTime(params.starttime) if params.starttime else None,
        endtime=UTCDateTime(params.endtime) if params.endtime else None,
        network=params.network,
        station=params.station,
        location=params.location,
        channel=params.channel,
        asquery=params.format in ("sql", "css"),
    )

    match params.format: # python 3.10+
        case "miniseed" | "sac.zip":
            if out:
                current_time = datetime.now().strftime("%Y-%m-%dt%H %M %S %fz")
                fname = FILENAME_FMT.format(
                    current_time=current_time,
                    file_extension=WAVEFORM_FORMATS[params.format].extension,
                )
                headers = {"Content-Disposition": f'attachment; filename="{fname}"'}
                content = WAVEFORM_FORMATS[params.format].convert_stream(out)
                mimetype = WAVEFORM_FORMATS[params.format].mimetype
                r = Response(
                    content=content,
                    media_type=mimetype,
                    headers=headers,
                )
            else:
                r = Response(status_code=int(params.nodata))

        case "sql":
            # return a string version of the literal SQL query, for debugging
            sqltxt = str(
                out.statement.compile(session.bind, compile_kwargs={"literal_binds": True})
            )
            r = Response(content=sqltxt, media_type="text/plain")

        case "css":
            Wfdisc, = _get_entities(out, 'Wfdisc')
            wfname = Wfdisc.__name__
            logger.info(f'{wfname=}')

            flatfile = "\n".join([str(getattr(row, wfname)) for row in out])
            if flatfile:
                r = PlainTextResponse(content=flatfile)
            else:
                r = Response(status_code=int(params.nodata))

    return r


# How to get the Swagger UI to offer a text box for the POST body:
# https://github.com/fastapi/fastapi/issues/1982#issuecomment-1104499366
@router.post("/query", summary="Download data using a properly-formatted request file")
async def dataselect_query_post(
    request: Request,
    body: str = Body(..., media_type='text/plain'),
    session: Session = Depends(db.get_db)
):
    """
    Parse dataselect POST format to issue query.

    Keyword parameters are currently ignored.

    A POST request could look like this:

    ```
    quality=M
    minimumlength=0.0
    longestonly=FALSE
    TA A25A -- BH? 2010-03-25T00:00:00 2010-03-28T00:00:00
    IU ANMO * BH? 2010-03-25T00:00:00 2010-03-28T00:00:00
    IU ANMO 10 HHZ 2010-03-25T00:00:00 2010-03-28T00:00:00
    II KURK 00 BH? 2010-03-25T00:00:00 2010-03-28T00:00:00
    ```

    Make the request using `wget` or `curl` like this:

    ```
    wget --post-file=request.txt -O out.mseed http://base_url/fdsnws/dataselect/1/query

    curl -L --data-binary @request.txt -o out.mseed http://base_url/fdsnws/dataselect/1/query
    ```

    """
    # body = await request.body()
    # body = body.decode('utf-8')
    try:
        params, bulk = post_parse(body.strip().split('\n'))
    except ValueError as e:
        # TODO: intercept ValueError to send our FDSN Error Response stuff
        msg = f'Unable to parse POST body: {e}'
        # raise ValueError(msg)
        raise RequestValidationError(msg)

    # TODO: put these into the exception handlers.
    logger.debug(f'{request.headers=}')
    logger.debug(f'{body=}')
    if bulk:
        queries = [
            {
                'network': network,
                'station': station,
                'location': location,
                'channel': channel,
                'starttime': starttime,
                'endtime': endtime,
            }
            for network, station, location, channel, starttime, endtime in bulk
        ]
    else:
        queries = [{}]

    # fill out each query with global parameters, overwriting if necessary
    # if no bulk lines were provided, only one query is present and will need to include required parameters
    queries = [dict(query, **params) for query in queries]

    # TODO: Make this use errors.FDSNErrorResponse and hook into FastAPI's handling
    # https://fastapi.tiangolo.com/tutorial/handling-errors/#install-custom-exception-handlers
    try:
        # Since we're not using FastAPI's builtin validation (we don't use JSON),
        # we have to do it ourselves by unpacking parameters in the DataselectQuery model.
        dataselect_queries = [DataselectQuery(**query) for query in queries]
    except ValidationError as e:
        # Also, The FDSNWS spec is pretty specific about errors:
        # http://www.fdsn.org/webservices/FDSN-WS-Specification-Commonalities-1.2.pdf
        # msg = FDSNErrorText(
        #     error_code=BAD_REQUEST.code,
        #     simple_descr=BAD_REQUEST.message,
        #     detail=str(e),
        #     service_docs_url=request.base_url,
        #     submitted_url=request['path'],
        #     utc_date_time=UTCDateTime(),
        #     service_version=VERSION,
        # )
        # return PlainTextResponse(
        #     content=str(msg),
        #     status_code=msg.error_code
        # )
        return BadRequestResponse(
            content=str(e),
            service_docs_url=request.base_url,
            submitted_url=request['path'],
            service_version=VERSION,
        )

    client = Client(session,
        affiliation=db.Affiliation,
        wfdisc=db.Wfdisc,
    )

    # full or empty Streams.
    out = [
        client.get_waveforms(
            q.network,
            q.station,
            q.location,
            q.channel,
            UTCDateTime(q.starttime),
            UTCDateTime(q.endtime),
        )
        for q in dataselect_queries
    ]

    # flatten and remove empty Streams
    # out is a single (possibly empty) Stream
    out = reduce(lambda a, b : a + b, out)
    logger.debug(f'{str(out)}')


    if out:
        current_time = datetime.now().strftime("%Y-%m-%dt%H %M %S %fz")
        fname = FILENAME_FMT.format(
            current_time=current_time,
            file_extension=WAVEFORM_FORMATS['miniseed'].extension,
        )
        headers = {"Content-Disposition": f'attachment; filename="{fname}"'}
        content = WAVEFORM_FORMATS['miniseed'].convert_stream(out)
        mimetype = WAVEFORM_FORMATS['miniseed'].mimetype
        r = Response(
            content=content,
            media_type=mimetype,
            headers=headers,
        )
    else:
        # TODO: replace with our custom FDSNErrorText stuff?
        r = Response(NO_DATA.message, status_code=int(params.get('nodata', NO_DATA.code)))

    return r
