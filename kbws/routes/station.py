"""FDSN station metadata routes."""
from importlib.resources import files
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, Request, Response
from fastapi.responses import PlainTextResponse
from obspy import Inventory, UTCDateTime
from pisces.fdsn import Client
from pisces.util import _get_entities
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .. import database as db
from ..formats import post_parse, station_text, station_xml_bytes
from ..models.station import StationLevel, StationQuery
from ..responses import (
    BAD_REQUEST,
    NO_DATA,
    NO_DATA_ALT,
    fdsn_response,
)
from ..services import require_service, require_tables

VERSION = "1.1.0"
MAJOR_VERSION = VERSION.split(".")[0]
router = APIRouter(
    prefix=f"/fdsnws/station/{MAJOR_VERSION}",
    tags=["station"],
    dependencies=[Depends(require_service("station"))],
)


def get_wadl():
    """Return the packaged station-service WADL document."""
    return files("kbws.routes").joinpath("station.xml").read_text(encoding="utf-8")


@router.get("/application.wadl", summary="Download the service WADL file")
def station_wadl(wadl: str = Depends(get_wadl)):
    return Response(content=wadl, media_type="application/xml")


@router.get("/version", response_class=PlainTextResponse)
def station_version():
    return VERSION


@router.get("/query")
def station_query(
    request: Request,
    params: Annotated[StationQuery, Query()],
    session: Session = Depends(db.get_db),
):
    """Query station metadata.

    Returns StationXML by default, or FDSN station text for network, station,
    and channel levels. The ``css`` format returns Site rows and ``sql``
    returns the generated SQL query.

    ### Example

    [/fdsnws/station/1/query?channel=BH?&endtime=2010-03-28&format=text&level=channel&network=TA&starttime=2010-03-25&station=A25A](/fdsnws/station/1/query?channel=BH?&endtime=2010-03-28&format=text&level=channel&network=TA&starttime=2010-03-25&station=A25A)

    """
    try:
        level_tables = {
            "channel": {"sitechan"},
            "response": {"sitechan", "sensor", "instrument"},
        }
        require_tables("station", level_tables.get(params.level.value, set()))
        out = Client(
            session,
            affiliation=db.Affiliation,
            instrument=db.Instrument,
            network=db.Network,
            sensor=db.Sensor,
            site=db.Site,
            sitechan=db.Sitechan,
        ).get_stations(
            starttime=UTCDateTime(params.starttime) if params.starttime else None,
            endtime=UTCDateTime(params.endtime) if params.endtime else None,
            network=params.network,
            station=params.station,
            channel=params.channel,
            # location is a core FDSN parameter, but Pisces currently ignores it.
            minlatitude=params.minlatitude,
            maxlatitude=params.maxlatitude,
            minlongitude=params.minlongitude,
            maxlongitude=params.maxlongitude,
            level=params.level.value,
            asquery=params.format in ("sql", "css") or params.asquery,
        )
    except (ValueError, TypeError) as exc:
        return fdsn_response(request, BAD_REQUEST, detail=str(exc), service_version=VERSION)

    if out:
        match params.format:
            case "xml":
                r = Response(
                    content=station_xml_bytes(out),
                    media_type="application/xml",
                )
            case "text":
                if params.level == "response":
                    r = fdsn_response(
                        request,
                        BAD_REQUEST,
                        detail="format=text is not supported for level=response",
                        service_version=VERSION,
                    )
                else:
                    r = Response(
                        content=station_text(out, params.level.value),
                        media_type="text/plain",
                    )
            case "sql":
                content = str(
                    out.statement.compile(
                        session.bind,
                        compile_kwargs={"literal_binds": True},
                    )
                )
                r = Response(content=content, media_type="text/plain")
            case "css":
                Site, = _get_entities(out, "Site")
                sitename = Site.__name__
                flatfile = "\n".join(str(getattr(row, sitename)) for row in out)
                r = PlainTextResponse(content=flatfile)
    else:
        r = fdsn_response(
            request,
            NO_DATA if params.nodata == "204" else NO_DATA_ALT,
            detail="",
            service_version=VERSION,
        )

    return r


@router.post("/query")
def station_query_post(
    request: Request,
    body: str = Body(..., media_type="text/plain"),
    session: Session = Depends(db.get_db),
):
    """Query station metadata using the FDSN station POST request format.

    The body may contain global ``key=value`` parameters followed by repeated
    ``NET STA LOC CHA STARTTIME ENDTIME`` selection rows.

    ### Example

    ```text
    format=text
    level=channel
    TA A25A -- BH? 2010-03-25T00:00:00 2010-03-28T00:00:00
    ```
    """
    try:
        global_params, bulk = post_parse(body.splitlines())
        queries = []
        for network, station, _location, channel, starttime, endtime in bulk:
            queries.append(StationQuery(
                **dict(
                    global_params,
                    network=network,
                    station=station,
                    channel=channel,
                    starttime=starttime,
                    endtime=endtime,
                )
            ))
        if not queries:
            queries = [StationQuery(**global_params)]
    except (ValueError, ValidationError) as exc:
        return fdsn_response(request, BAD_REQUEST, detail=str(exc), service_version=VERSION)

    try:
        required = set()
        for query in queries:
            required.update({
                "sitechan" if query.level in ("channel", "response") else None,
                "sensor" if query.level == "response" else None,
                "instrument" if query.level == "response" else None,
            } - {None})
        require_tables("station", required)
        client = Client(
            session,
            affiliation=db.Affiliation,
            instrument=db.Instrument,
            network=db.Network,
            sensor=db.Sensor,
            site=db.Site,
            sitechan=db.Sitechan,
        )
        results = [client.get_stations(
            starttime=UTCDateTime(query.starttime) if query.starttime else None,
            endtime=UTCDateTime(query.endtime) if query.endtime else None,
            network=query.network,
            station=query.station,
            channel=query.channel,
            # location is a core FDSN parameter, but Pisces currently ignores it.
            minlatitude=query.minlatitude,
            maxlatitude=query.maxlatitude,
            minlongitude=query.minlongitude,
            maxlongitude=query.maxlongitude,
            level=StationLevel(query.level).value,
            asquery=query.format in ("sql", "css") or query.asquery,
        ) for query in queries]
    except (ValueError, TypeError) as exc:
        return fdsn_response(request, BAD_REQUEST, detail=str(exc), service_version=VERSION)
    format = queries[0].format
    if not results:
        r = fdsn_response(
            request,
            NO_DATA if queries[0].nodata == "204" else NO_DATA_ALT,
            detail="",
            service_version=VERSION,
        )
    else:
        match format:
            case "xml":
                inventories = [result for result in results if isinstance(result, Inventory)]
                if not any(inventories):
                    r = fdsn_response(
                        request,
                        NO_DATA if queries[0].nodata == "204" else NO_DATA_ALT,
                        detail="",
                        service_version=VERSION,
                    )
                else:
                    combined = Inventory(
                        networks=[
                            network
                            for result in inventories
                            for network in result.networks
                        ]
                    )
                    r = Response(
                        content=station_xml_bytes(combined),
                        media_type="application/xml",
                    )
            case "text":
                inventories = [result for result in results if isinstance(result, Inventory)]
                if not any(inventories):
                    r = fdsn_response(
                        request,
                        NO_DATA if queries[0].nodata == "204" else NO_DATA_ALT,
                        detail="",
                        service_version=VERSION,
                    )
                elif queries[0].level == "response":
                    r = fdsn_response(
                        request,
                        BAD_REQUEST,
                        detail="format=text is not supported for level=response",
                        service_version=VERSION,
                    )
                else:
                    r = Response(
                        content="".join(
                            station_text(
                                inventory,
                                StationLevel(queries[0].level).value,
                            )
                            for inventory in inventories
                        ),
                        media_type="text/plain",
                    )
            case "sql":
                r = PlainTextResponse(content="\n".join(
                    str(result.statement.compile(
                        session.bind,
                        compile_kwargs={"literal_binds": True},
                    ))
                    for result in results
                ))
            case "css":
                rows = []
                for result in results:
                    Site, = _get_entities(result, "Site")
                    sitename = Site.__name__
                    rows.extend(str(getattr(row, sitename)) for row in result)
                if not rows:
                    r = fdsn_response(
                        request,
                        NO_DATA if queries[0].nodata == "204" else NO_DATA_ALT,
                        detail="",
                        service_version=VERSION,
                    )
                else:
                    r = PlainTextResponse(content="\n".join(rows))

    return r
