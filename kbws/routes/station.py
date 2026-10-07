"""
Functions that translate parsed HTTP station request arguements from FastAPI to
database queries, and return Inventory objects.

"""
import io
from typing import Annotated
from functools import reduce

from fastapi import APIRouter, Response, Depends, Request
from fastapi.responses import PlainTextResponse, RedirectResponse
import starlette.status as status
from sqlalchemy.orm import Session
from obspy import Inventory, UTCDateTime
from pisces import request
from pydantic import ValidationError

from .. import database as db
from ..responses import FDSNErrorText, BAD_REQUEST
from ..models import StationQuery
from ..formats import post_parse

# HTTP 413 status shall be returned when either the request entity itself is too large or the resulting data set would be too large
# TOO_LARGE_EXCEPTION = HTTPException(detail='Request or result is too large.', status_code=413)

VERSION = "1.1.0"
MAJOR_VERSION = VERSION.split(".")[0]

def _inventory_to_stationxml_string(inventory: Inventory) -> str:
    with io.BytesIO() as fp:
        inventory.write(fp, format="STATIONXML")
        fp.seek(0)
        out = fp.read()
    return out




def query_database(session: Session, params: StationQuery, **tables):
    """ Params follows the StationQuery model. """
    t1 = int(UTCDateTime(params.starttime).strftime('%Y%j')) if params.starttime else None
    t2 = int(UTCDateTime(params.endtime).strftime('%Y%j')) if params.endtime else None
    out = request.get_stations(
        session,
        tables['site'],
        tables.get('sitechan'),
        tables.get('affiliation'),
        stations=[params.station],
        channels=[params.channel],
        nets=[params.network],
        region=(
            params.minlongitude,
            params.maxlongitude,
            params.minlatitude,
            params.maxlatitude,
        ),
        time_span=(t1, t2),
        asquery=params.asquery,
    )

    return out


# All subsequent routes originate at this path
router = APIRouter(prefix=f"/fdsnws/station/{MAJOR_VERSION}", tags=['station'])


@router.get("/version", response_class=PlainTextResponse)
def station_version():
    return VERSION


@router.get("/query")
def station_query(
    params: Annotated[StationQuery, Depends()],
    session: Session = Depends(db.get_db)
):
    """
    Event query docstring.

    """
    out = query_database(session, params, site=db.Site, sitechan=db.Sitechan, affiliation=db.Affiliation)


    if params.asquery:
        sql = str(
            out.statement.compile(session.bind, compile_kwargs={"literal_binds": True})
        )
        r = Response(content=sql, media_type="text/plain")
    else:
        flatfile = "\n".join([str(row) for row in out])
        if flatfile:
            r = Response(content=flatfile, media_type="plain/text")
            # content = _catalog_to_quakeml_string(read_events())
            # r = Response(content=content, media_type='application/xml')
        else:
            # no data
            # TODO: add errors.FDSNErrorText usage here.
            r = Response(status_code=int(params.nodata))

    return r

    # return RedirectResponse(
    #     url=
    # )


# The IRIS page on POST offers examples using wget or curl that imply that data
# are sent as "form" data, which are of type application/x-www-form-urlencoded.
# FastAPI is built for JSON, so we have to find the small corner of its documentation
# that describe accepting and parsing/reading arbitrary form data to supply to the endpoint
# function.

# async def station_query_post(request: Request):
@router.post("/query")
async def station_query_post(
    request: Request,
    session: Session = Depends(db.get_db)
):
    """
    Parse the station POST format, query the database, and build an Inventory object from the results.

    A POST request could look like this:
    ```
    level=channel
    format=text
    TA A25A -- BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
    IU ANMO * BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
    IU ANMO 10 HHZ 2010-03-25T00:00:00 2010-04-01T00:00:00
    II KURK 00 BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
    ```

    Each row is a seperate query, as a combination of the required paremeters from the row with
    top-level global parameters.

    Currently only returns the body of the POST.

    """
    # https://stackoverflow.com/a/70879659/745557
    body = await request.body()
    body = body.decode('utf-8')
    params, bulk = post_parse(body.strip().split('\n'))
    # print(f'body:\n{body}')
    # print(f'headers:\n{request.headers}')

    # here, we need to handle input validation, as FastAPI can't do it for us.
    # TODO: make sure params aren't repeated.
    excluded = ('startbefore', 'endbefore', 'startafter', 'endafter')
    if any(key in params for key in excluded):
        e = FDSNErrorText(
            error_code=BAD_REQUEST.code,
            simple_descr=BAD_REQUEST.message,
            detail=f"POST parameters cannot contain any of the following: {excluded}",
            service_docs_uri=request.base_url,
            submitted_url=body,
            utc_date_time=UTCDateTime(),
            service_version=VERSION,
        )
        return  PlainTextResponse(content=str(e), status_code=e.error_code)

    if bulk:
        queries = [
            {
                'network': network,
                'station': station,
                'channel': channel,
                'starttime': starttime,
                'endtime': endtime,
            }
            for network, station, location, channel, starttime, endtime in bulk
        ]
    else:
        queries = [{}]

    # update each query with global parameters, overwriting if necessary
    # if no bulk lines were provided, only one query is present and will need to include required parameters
    queries = [dict(query, **params) for query in queries]

    # validate and cast types.
    # Since we're not using FastAPI's builtin validation (we don't use JSON),
    # we have to do it ourselves. Also, The FDSNWS spec is pretty specific about errors:
    # http://www.fdsn.org/webservices/FDSN-WS-Specification-Commonalities-1.2.pdf
    try:
        station_queries = [StationQuery(**query) for query in queries]
    except ValidationError as e:
        msg = FDSNErrorText(
            error_code=BAD_REQUEST.code,
            simple_descr=BAD_REQUEST.message,
            detail=str(e),
            service_docs_uri=request.base_url,
            submitted_url=request['path'],
            utc_date_time=UTCDateTime(),
            service_version=VERSION,
        )
        return PlainTextResponse(content=msg, status_code=BAD_REQUEST.code)

    # list of lists (results), excluding empty
    out = [
            query_database(session, sq, site=db.Site, sitechan=db.Sitechan, affiliation=db.Affiliation)
            for sq in station_queries
           ]

    # flatten and remove empty result lists
    out = reduce(lambda a, b : a + b, out)

    # how to remove duplicates?  sets don't work b/c SQLA results are unhashable
    # out = _dedupe(out)

    print(out)

    return Response(content=body, media_type="plain/text")
