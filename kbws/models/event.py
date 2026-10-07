""" Models for event API endpoints.
"""
from enum import Enum
from typing import Annotated, Optional
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field
from fastapi import Query

from .common import NoData

class EventFormat(str, Enum):
    xml = "xml"
    css = "css"
    text = "text"
    json = "json"
    sql = "sql"


# the Pydantic query parameter model for the FastAPI events endpoint
# TODO: make some params required following https://www.fdsn.org/webservices/fdsnws-event-1.2.pdf
class EventQuery(BaseModel):
    starttime: Annotated[
        Optional[datetime | date],
        Field(
            description=(
                "Limit results to events occurring on or after the specified start time, "
                "using `ISO8601` format YYYY-MM-DDThh:mm:ss[.ssssss]"
            ),
            examples="2012-11-01T00:00:00.000",
        ),
    ] = None
    endtime: Annotated[
        Optional[datetime | date],
        Field(
            description=(
                "Limit results to events occurring on or before the specified end time, "
                "using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]"
            ),
            examples="2012-11-03",
        ),
    ] = None
    updatedafter: Annotated[
        Optional[datetime | date],
        Field(
            description=(
                "Limit to events updated after the specified time, "
                "using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]"
            ),
            examples="2012-11-03",
        ),
    ] = None
    minlatitude: Annotated[
        Optional[float],
        Field(
            description="Limit to events with a latitude larger than or equal to the specified minimum.",
            ge=-90.0,
            le=90.0,
            examples=40.1,
        ),
    ] = None
    maxlatitude: Annotated[
        Optional[float],
        Field(
            description="Limit to events with a latitude smaller than or equal to the specified maximum.",
            ge=-90.0,
            le=90.0,
            examples=46.9,
        ),
    ] = None
    minlongitude: Annotated[
        Optional[float],
        Field(
            description="Limit to events with a longitude larger than or equal to the specified minimum.",
            ge=-180.0,
            le=180.0,
            examples=-10.5,
        ),
    ] = None
    maxlongitude: Annotated[
        Optional[float],
        Field(
            description="Limit to events with a longitude smaller than or equal to the specified maximum.",
            ge=-180.0,
            le=180.0,
            examples=5.3,
        ),
    ] = None
#     latitude: Annotated[
#         float,
#         Query(
#             description="Specify the latitude to be used for a radius search.",
#             ge=-90.0,
#             le=90.0,
#             examples=46.9,
#         ),
#     ] = 0
#     longitude: Annotated[
#         float,
#         Query(
#             description="Specify the longitude to be used for a radius search.",
#             ge=-180.0,
#             le=180.0,
#             examples=5.3,
#         ),
#     ] = 0
#     minradius: Annotated[
#         float,
#         Query(
#             description="Limit to events within the specified minimum number of degrees from the geographic point defined by the latitude and longitude parameters.",
#             ge=0.0,
#             le=180.0,
#             examples=1.3,
#         ),
#     ] = 0
#     maxradius: Annotated[
#         float,
#         Query(
#             description="Limit to events within the specified maximum number of degrees from the geographic point defined by the latitude and longitude parameters.",
#             ge=0.0,
#             le=180.0,
#             examples=5.1,
#         ),
#     ] = 0
    mindepth: Annotated[
        Optional[float],
        Field(
            description="Limit to events with depth more than the specified minimum, in kilometers.",
            examples=1.3,
        ),
    ] = None
    maxdepth: Annotated[
        Optional[float],
        Field(
            description="Limit to events with depth less than the specified maximum, in kilometers.",
            examples=100,
        ),
    ] = None
    minmagnitude: Annotated[
        Optional[float],
        Field(
            description="Limit to events with a magnitude larger than the specified minimum.",
            examples=-1.0,
        ),
    ] = None
    maxmagnitude: Annotated[
        Optional[float],
        Field(
            description="Limit to events with a magnitude smaller than the specified maximum.",
            examples=8.3,
        ),
    ] = None
    magnitudetype: Annotated[
        Optional[str],
        Query(
            description="Specify a magnitude type to use for testing the minimum and maximum limits. ex. ML Ms mb Mw all preferred",
            examples="Mw",
        ),
    ] = None
    eventtype: Annotated[
        Optional[str],
        Field(
            description="Limit to events with a specified eventType. The parameter value can be a single item, a comma-separated list of items. Allowed values are from QuakeML or unknown if eventType is not given.",
            examples="Mw",
        ),
    ] = None
    includeallorigins: Annotated[
        bool,
        Field(
            description="Specify if all origins for the event should be included, default is data center dependent but is suggested to be the preferred origin only.",
        ),
    ] = False
    # includeallmagnitudes: Annotated[
    #     bool,
    #     Query(
    #         description="Specify if all magnitudes for the event should be included, default is data center dependent but is suggested to be the preferred magnitude only.",
    #     ),
    # ] = False
    includearrivals: Annotated[
        bool,
        Field(
            description="Specify if phase arrivals should be included",
        ),
    ] = False
    eventid: Annotated[
        Optional[str],
        Field(
            description="Select a specific event by ID; event identifiers are data center specific. Corresponds to an evid, returns a prefor.",
            examples="5659275",
        ),
    ] = None
    nodata: Annotated[
        NoData,
        Field(
            description="Select status code for “no data”, either 204 (default) or 404"
        ),
    ] = '204'
    format: Annotated[
        EventFormat,
        Field(
            description=(
                "Specify format of result: xml (default) is QuakeML, text (described in FDSN specification, not yet implemented), "
                "css (text Origin table rows), json, or sql (the SQL query that was built, not the results)."
            )
        ),
    ] = "xml"

    model_config = ConfigDict(extra='ignore')
