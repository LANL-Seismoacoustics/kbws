"""Models for the station API endpoint."""
from datetime import date, datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from .common import NoData


class StationFormat(str, Enum):
    xml = "xml"
    text = "text"
    css = "css"
    sql = "sql"


class StationLevel(str, Enum):
    network = "network"
    station = "station"
    channel = "channel"
    response = "response"


# the Pydantic query parameter model for the FastAPI station endpoint
class StationQuery(BaseModel):
    starttime: Annotated[
        datetime | date | None,
        Field(
            description=(
                "Limit results to metadata operating on or after the specified start time, "
                "using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]"
            ),
            examples="2012-11-01T00:00:00.000",
        ),
    ] = None
    endtime: Annotated[
        datetime | date | None,
        Field(
            description=(
                "Limit results to metadata operating on or before the specified end time, "
                "using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]"
            ),
            examples="2012-11-03",
        ),
    ] = None
    # shortcut: Pisces does not implement epoch-specific filters yet.
    # startbefore: Annotated[Optional[datetime | date], Field(description="Limit to metadata epochs starting before this time.")] = None
    # startafter: Annotated[Optional[datetime | date], Field(description="Limit to metadata epochs starting after this time.")] = None
    # endbefore: Annotated[Optional[datetime | date], Field(description="Limit to metadata epochs ending before this time.")] = None
    # endafter: Annotated[Optional[datetime | date], Field(description="Limit to metadata epochs ending after this time.")] = None
    network: Annotated[
        str | None,
        Field(
            description="Select one or more network codes. Multiple codes are comma-separated.",
            examples="IU",
        ),
    ] = None
    station: Annotated[
        str | None,
        Field(
            description="Select one or more station codes. Multiple codes are comma-separated.",
            examples="ANMO",
        ),
    ] = None
    location: Annotated[
        str | None,
        Field(
            description=(
                "Select one or more location identifiers. Pisces currently accepts this "
                "FDSN parameter but does not apply it."
            ),
            examples="00",
        ),
    ] = None
    channel: Annotated[
        str | None,
        Field(
            description="Select one or more channel codes. Multiple codes are comma-separated.",
            examples="BH1",
        ),
    ] = None
    minlatitude: Annotated[
        float | None,
        Field(
            description="Limit to stations with latitude greater than or equal to this value.",
            ge=-90.0,
            le=90.0,
            examples=40.1,
        ),
    ] = None
    maxlatitude: Annotated[
        float | None,
        Field(
            description="Limit to stations with latitude less than or equal to this value.",
            ge=-90.0,
            le=90.0,
            examples=46.9,
        ),
    ] = None
    minlongitude: Annotated[
        float | None,
        Field(
            description="Limit to stations with longitude greater than or equal to this value.",
            ge=-180.0,
            le=180.0,
            examples=-10.5,
        ),
    ] = None
    maxlongitude: Annotated[
        float | None,
        Field(
            description="Limit to stations with longitude less than or equal to this value.",
            ge=-180.0,
            le=180.0,
            examples=5.3,
        ),
    ] = None
    # shortcut: Pisces does not implement radius searches yet.
    # latitude: Annotated[Optional[float], Field(description="Latitude for a radius search.", ge=-90.0, le=90.0)] = None
    # longitude: Annotated[Optional[float], Field(description="Longitude for a radius search.", ge=-180.0, le=180.0)] = None
    # minradius: Annotated[Optional[float], Field(description="Minimum radius in degrees.", ge=0.0, le=180.0)] = None
    # maxradius: Annotated[Optional[float], Field(description="Maximum radius in degrees.", ge=0.0, le=180.0)] = None
    level: Annotated[
        StationLevel,
        Field(description="Specify the level of detail for the results."),
    ] = "station"
    # shortcut: Pisces does not implement these metadata/availability filters yet.
    # includerestricted: Annotated[bool, Field(description="Include restricted stations.")] = False
    # includeavailability: Annotated[bool, Field(description="Include time-series availability.")] = False
    # updatedafter: Annotated[Optional[datetime | date], Field(description="Limit metadata updated after this time.")] = None
    # matchtimeseries: Annotated[bool, Field(description="Require matching time-series data.")] = False
    nodata: Annotated[
        NoData,
        Field(description="Select status code for no data, either 204 (default) or 404."),
    ] = "204"
    format: Annotated[
        StationFormat,
        Field(
            description=(
                "Specify the result format: xml (StationXML), text (FDSN station text), "
                "css (CSS Site rows), or sql (the generated SQL query)."
            )
        ),
    ] = "xml"
    asquery: Annotated[
        bool,
        Field(description="Return the database query instead of normal output."),
    ] = False

    model_config = ConfigDict(extra="ignore")
