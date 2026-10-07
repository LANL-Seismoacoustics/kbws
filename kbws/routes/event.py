"""
Functions that translate parsed HTTP event request arguements from FastAPI to
database queries, and return text or ObsPy Catalog objects.

"""
from typing import Annotated

from fastapi import APIRouter, Response, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from obspy import UTCDateTime
from pisces.fdsn import Client
from pisces.util import _get_entities

from .. import database as db
from ..models import EventQuery
from ..formats import catalog_xml, catalog_json

VERSION = "1.2.0"
MAJOR_VERSION = VERSION.split(".")[0]

# TODO: add this to package data during installation
def get_wadl():
    """Return the WADL text, but cache it, so subsequent calls don't hit the disk."""
    with open("kbws-events.xml", "r") as wadl_file:
        return wadl_file.read()


# All subsequent routes originate at this path
router = APIRouter(prefix=f"/fdsnws/event/{MAJOR_VERSION}", tags=['event'])


@router.get("/application.wadl", summary="Download the service WADL file")
def event_wadl(wadl: str = Depends(get_wadl)):
    return Response(content=wadl, media_type="application/xml")


@router.get("/version", response_class=PlainTextResponse)
def event_version():
    return VERSION


@router.get("/query")
def event_query(
    params: Annotated[EventQuery, Query()],
    session: Session = Depends(db.get_db)
):
    """Event query URL builder.

    ### Example

    [http://0.0.0.0:8000/fdsnws/event/1/query?endtime=2012-11-03T01%3A00%3A00.00&maxdepth=100&maxlatitude=47&maxlongitude=5&mindepth=1.3&minlatitude=40&minlongitude=-10&starttime=2012-11-01](http://0.0.0.0:8000/fdsnws/event/1/query?endtime=2012-11-03T01%3A00%3A00.00&maxdepth=100&maxlatitude=47&maxlongitude=5&mindepth=1.3&minlatitude=40&minlongitude=-10&starttime=2012-11-01)

    """
    client = Client(session,
        event=db.Event,
        origin=db.Origin,
        netmag=db.Netmag,
        stamag=db.Stamag,
        arrival=db.Arrival,
        assoc=db.Assoc,
    )

    # this endpoint is easy, as all parameters map directly to the pisces FDSN Client.get_events
    out = client.get_events(
        starttime=UTCDateTime(params.starttime) if params.starttime else None,
        endtime=UTCDateTime(params.endtime) if params.endtime else None,
        updatedafter=UTCDateTime(params.updatedafter) if params.updatedafter else None,
        minlongitude=params.minlongitude,
        maxlongitude=params.maxlongitude,
        minlatitude=params.minlatitude,
        maxlatitude=params.maxlatitude,
        mindepth=params.mindepth,
        maxdepth=params.maxdepth,
        includeallorigins=params.includeallorigins,
        includearrivals=params.includearrivals,
        eventid=params.eventid,
        asquery=params.format in ("sql", "css"),
    )

    if out:
        match params.format:
            case "xml":
                content = catalog_xml(out)
                r = Response(content=content, media_type='application/xml')
            case "json":
                content = catalog_json(out)
                r = Response(content=content, media_type='application/json')
            case "sql":
                sqltxt = str(
                    out.statement.compile(session.bind, compile_kwargs={"literal_binds": True})
                )
                r = Response(content=sqltxt, media_type="text/plain")
            case "css":
                # TODO: make this output better than just an origin table
                # this format can stream, as each line is independent. Consider using StreamingResponse:
                # https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse

                # get the query's Origin table class and find out it's class name,
                # so instances of it can be pulled from each result row.
                Origin, = _get_entities(out, 'Origin')
                originname = Origin.__name__

                flatfile = "\n".join([str(getattr(row, originname)) for row in out])
                r = PlainTextResponse(content=flatfile)
    else:
        # TODO: use our custom formatted FDSN response stuff
        r = Response(status_code=int(params.nodata))

    return r


# TODO: for queryauth, to this: https://stackoverflow.com/a/62280245/745557
