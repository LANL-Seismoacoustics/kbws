from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query, Request, Response
from fastapi.responses import PlainTextResponse
from obspy import UTCDateTime
from pisces.fdsn import Client
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .. import database as db
from ..formats import (
    availability_json,
    availability_request,
    availability_text,
    post_parse,
)
from ..logging import get_logger
from ..models import AvailabilityExtent, AvailabilityQuery
from ..responses import (
    BAD_REQUEST,
    NO_DATA,
    NO_DATA_ALT,
    PISCES_GET_AVAILABILITY_ERRORS,
    REQUEST_TOO_LARGE,
    fdsn_response,
)

VERSION = "1.0.0"
MAJOR_VERSION = VERSION.split(".")[0]

logger = get_logger(__name__)

# All subsequent routes originate at this path
router = APIRouter(prefix=f"/fdsnws/availability/{MAJOR_VERSION}", tags=['availability'])


def _availability_kwargs(params, *, query: bool = False) -> dict:
    kwargs = {
        "network": params.network,
        "station": params.station,
        "channel": params.channel,
        "starttime": UTCDateTime(params.starttime),
        "endtime": UTCDateTime(params.endtime),
        "includerestricted": params.includerestricted,
    }

    if query:
        kwargs.update(
            mergegaps=params.mergegaps,
            show=params.show,
            # The FDSN flag groups all sample rates; the backend takes a tolerance.
            # Quality and overlap merging are not implemented yet.
            mergesamplerate=float("inf") if params.merge and "samplerate" in params.merge.split(",") else None,
        )

    return kwargs


@router.get("/version", response_class=PlainTextResponse)
def availability_version():
    return VERSION


@router.get("/extent")
def availability_extent(
    request: Request,
    params: Annotated[AvailabilityExtent, Query()],
    session: Session = Depends(db.get_db)
):
    """Earlies and latest time series holdings

    ### Example

    [/fdsnws/availability/1/extent?channel=BH?&endtime=2010-03-28&location=--&network=TA&starttime=2010-03-25&station=A25A](/fdsnws/availability/1/extent?channel=BH?&endtime=2010-03-28&location=--&network=TA&starttime=2010-03-25&station=A25A)

    """
    try:
        rows = Client(
            session,
            affiliation=db.Affiliation,
            wfdisc=db.Wfdisc,
            site=db.Site,
            network=db.Network,
        ).get_extent(**_availability_kwargs(params)).all()
    except PISCES_GET_AVAILABILITY_ERRORS[BAD_REQUEST] as exc:
        return fdsn_response(
            request, BAD_REQUEST, detail=str(exc), service_version=VERSION
        )

    if not rows:
        return fdsn_response(
            request,
            NO_DATA if params.nodata == "204" else NO_DATA_ALT,
            detail="",
            service_version=VERSION,
        )

    match params.format:
        case "json":
            content = availability_json(rows, extent=True)
            media_type = "application/json"
        case "text":
            content = availability_text(rows, extent=True)
            media_type = "text/plain"
        case "request":
            content = availability_request(rows)
            media_type = "text/plain"
    return Response(content=content, media_type=media_type)


@router.post("/extent")
def availability_extent_post(
    request: Request,
    body: str = Body(..., media_type="text/plain"),
    session: Session = Depends(db.get_db)
):
    """Query URL builder

    ### Example

    Add POST file example here.

    """
    lines = body.splitlines()
    if len(lines) > 100:
        return fdsn_response(
            request,
            REQUEST_TOO_LARGE,
            detail="POST body exceeds the 100-line limit.",
            service_version=VERSION,
        )

    try:
        global_params, bulk = post_parse(lines)
        params = [
            AvailabilityExtent(
                **dict(
                    {
                        "network": network,
                        "station": station,
                        "location": location,
                        "channel": channel,
                        "starttime": starttime,
                        "endtime": endtime,
                    },
                    **global_params,
                )
            )
            for network, station, location, channel, starttime, endtime in bulk
        ]
    except (ValueError, ValidationError) as exc:
        return fdsn_response(
            request, BAD_REQUEST, detail=str(exc), service_version=VERSION
        )

    if not params:
        nodata = global_params.get("nodata", "204")
        return fdsn_response(
            request,
            NO_DATA if nodata == "204" else NO_DATA_ALT,
            detail="",
            service_version=VERSION,
        )

    client = Client(
        session,
        affiliation=db.Affiliation,
        wfdisc=db.Wfdisc,
        site=db.Site,
        network=db.Network,
    )
    rows = []
    try:
        for param in params:
            rows.extend(client.get_extent(**_availability_kwargs(param)).all())
    except PISCES_GET_AVAILABILITY_ERRORS[BAD_REQUEST] as exc:
        return fdsn_response(
            request, BAD_REQUEST, detail=str(exc), service_version=VERSION
        )

    if not rows:
        return fdsn_response(
            request,
            NO_DATA if params[0].nodata == "204" else NO_DATA_ALT,
            detail="",
            service_version=VERSION,
        )

    match params[0].format:
        case "json":
            content = availability_json(rows, extent=True)
            media_type = "application/json"
        case "text":
            content = availability_text(rows, extent=True)
            media_type = "text/plain"
        case "request":
            content = availability_request(rows)
            media_type = "text/plain"
    return Response(content=content, media_type=media_type)


@router.post("/query")
def availability_query_post(
    request: Request,
    body: str = Body(..., media_type="text/plain"),
    session: Session = Depends(db.get_db)
):
    """Query URL builder

    ### Example

    Add POST file example here.

    """
    lines = body.splitlines()
    if len(lines) > 100:
        return fdsn_response(
            request,
            REQUEST_TOO_LARGE,
            detail="POST body exceeds the 100-line limit.",
            service_version=VERSION,
        )

    try:
        global_params, bulk = post_parse(lines)
        params = [
            AvailabilityQuery(
                **dict(
                    {
                        "network": network,
                        "station": station,
                        "location": location,
                        "channel": channel,
                        "starttime": starttime,
                        "endtime": endtime,
                    },
                    **global_params,
                )
            )
            for network, station, location, channel, starttime, endtime in bulk
        ]
    except (ValueError, ValidationError) as exc:
        return fdsn_response(
            request, BAD_REQUEST, detail=str(exc), service_version=VERSION
        )

    if not params:
        nodata = global_params.get("nodata", "204")
        return fdsn_response(
            request,
            NO_DATA if nodata == "204" else NO_DATA_ALT,
            detail="",
            service_version=VERSION,
        )

    client = Client(
        session,
        affiliation=db.Affiliation,
        wfdisc=db.Wfdisc,
        site=db.Site,
        network=db.Network,
    )
    rows = []
    try:
        for param in params:
            rows.extend(
                client.get_availability(
                    **_availability_kwargs(param, query=True)
                )
            )
    except PISCES_GET_AVAILABILITY_ERRORS[BAD_REQUEST] as exc:
        return fdsn_response(
            request, BAD_REQUEST, detail=str(exc), service_version=VERSION
        )

    if not rows:
        return fdsn_response(
            request,
            NO_DATA if params[0].nodata == "204" else NO_DATA_ALT,
            detail="",
            service_version=VERSION,
        )

    match params[0].format:
        case "json":
            content = availability_json(rows, extent=False, show=params[0].show)
            media_type = "application/json"
        case "text":
            content = availability_text(rows, extent=False, show=params[0].show)
            media_type = "text/plain"
        case "request":
            content = availability_request(rows)
            media_type = "text/plain"
    return Response(content=content, media_type=media_type)


@router.get("/query")
def availability_query(
    request: Request,
    params: Annotated[AvailabilityQuery, Query()],
    session: Session = Depends(db.get_db)
):
    """Query URL builder

    ### Example

    [/fdsnws/availability/1/query?channel=BH?&endtime=2010-03-28&location=--&network=TA&starttime=2010-03-25&station=A25A](/fdsnws/availability/1/query?channel=BH?&endtime=2010-03-28&location=--&network=TA&starttime=2010-03-25&station=A25A)

    """
    try:
        rows = Client(
            session,
            affiliation=db.Affiliation,
            wfdisc=db.Wfdisc,
            site=db.Site,
            network=db.Network,
        ).get_availability(**_availability_kwargs(params, query=True))
    except PISCES_GET_AVAILABILITY_ERRORS[BAD_REQUEST] as exc:
        return fdsn_response(
            request, BAD_REQUEST, detail=str(exc), service_version=VERSION
        )

    if not rows:
        return fdsn_response(
            request,
            NO_DATA if params.nodata == "204" else NO_DATA_ALT,
            detail="",
            service_version=VERSION,
        )

    match params.format:
        case "json":
            content = availability_json(rows, extent=False, show=params.show)
            media_type = "application/json"
        case "text":
            content = availability_text(rows, extent=False, show=params.show)
            media_type = "text/plain"
        case "request":
            content = availability_request(rows)
            media_type = "text/plain"
    return Response(content=content, media_type=media_type)
