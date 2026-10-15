""" Models for the station API endpoint.

NOTE: pisces station query support (`StationQuery.inventory()`/`request.get_stations`) is not yet
implemented. These models declare the full FDSN station parameter set for API-contract purposes,
but `routes/station.py` does not yet wire up all of them to a database query. Implementation is
deferred; keep this model in sync with the FDSN spec regardless.

"""
from enum import Enum
from typing import Annotated, Optional
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field

from .common import NoData


class StationFormat(str, Enum):
    xml = "xml"
    css = "css"
    text = "text"


class StationLevel(str, Enum):
    network = "network"
    station = "station"
    channel = "channel"
    response = "response"


# the Pydantic query parameter model for the FastAPI station endpoint
class StationQuery(BaseModel):
    starttime: Annotated[
        Optional[datetime | date],
        Field(
            description=(
                "Limit results to channels operating on or after the specified start time, "
                "using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]"
            ),
            examples="2012-11-01T00:00:00.000",
        ),
    ] = None
    endtime: Annotated[
        Optional[datetime | date],
        Field(
            description=(
                "Limit results to channels operating on or before the specified end time, "
                "using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]"
            ),
            examples="2012-11-03",
        ),
    ] = None
#     startbefore: Annotated[
#         Optional[datetime | date],
#         Field(
#             description="Limit to metadata epochs starting before specified time. Applied to channel epochs, using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]",
#             examples="2012-11-03",
#         ),
#     ] = None
#     startafter: Annotated[
#         Optional[datetime | date],
#         Field(
#             description="Limit to metadata epochs starting after specified time. Applied to channel epochs, using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]",
#             examples="2012-11-03",
#         ),
#     ] = None
#     endbefore: Annotated[
#         Optional[datetime | date],
#         Field(
#             description="Limit to metadata epochs ending before specified time. Applied to channel epochs, using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]",
#             examples="2012-11-03",
#         ),
#     ] = None
#     endafter: Annotated[
#         Optional[datetime | date],
#         Field(
#             description="Limit to metadata epochs ending after specified time. Applied to channel epochs, using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]",
#             examples="2012-11-03",
#         ),
#     ] = None
    network: Annotated[
        str,
        Field(
            description="Select one or more network codes. Can be SEED network codes or data center defined codes. Multiple codes are comma-separated",
            examples="IU",
        ),
    ] = ...
    station: Annotated[
        str,
        Field(
            description="Select one or more SEED station codes. Multiple codes are comma-separated",
            examples="ANMO",
        ),
    ] = ...
#     location: Annotated[
#         str,
#         Field(
#             description="Select one or more SEED location identifiers. Multiple identifiers are comma-separated. As a special case '--' (two dashes) will be translated to a string of two space characters to match blank location IDs.",
#             examples="00",
#         ),
#     ] = ...
    channel: Annotated[
        str,
        Field(
            description="Select one or more SEED channel codes. Multiple codes are comma-separated.",
            examples="BH1",
        ),
    ] = ...
    minlatitude: Annotated[
        Optional[float],
        Field(
            description="Limit to stations with a latitude larger than or equal to the specified minimum.",
            ge=-90.0,
            le=90.0,
            examples=40.1,
        ),
    ] = None
    maxlatitude: Annotated[
        Optional[float],
        Field(
            description="Limit to stations with a latitude smaller than or equal to the specified maximum.",
            ge=-90.0,
            le=90.0,
            examples=46.9,
        ),
    ] = None
    minlongitude: Annotated[
        Optional[float],
        Field(
            description="Limit to stations with a longitude larger than or equal to the specified minimum.",
            ge=-180.0,
            le=180.0,
            examples=-10.5,
        ),
    ] = None
    maxlongitude: Annotated[
        Optional[float],
        Field(
            description="Limit to stations with a longitude smaller than or equal to the specified maximum.",
            ge=-180.0,
            le=180.0,
            examples=5.3,
        ),
    ] = None
#     latitude: Annotated[
#         Optional[float],
#         Field(
#             description="Specify the latitude to be used for a radius search.",
#             ge=-90.0,
#             le=90.0,
#             examples=46.9,
#         ),
#     ] = None
#     longitude: Annotated[
#         Optional[float],
#         Field(
#             description="Specify the longitude to be used for a radius search.",
#             ge=-180.0,
#             le=180.0,
#             examples=5.3,
#         ),
#     ] = None
#     minradius: Annotated[
#         Optional[float],
#         Field(
#             description="Limit to stations within the specified minimum number of degrees from the geographic point defined by the latitude and longitude parameters.",
#             ge=0.0,
#             le=180.0,
#             examples=1.3,
#         ),
#     ] = None
#     maxradius: Annotated[
#         Optional[float],
#         Field(
#             description="Limit to stations within the specified maximum number of degrees from the geographic point defined by the latitude and longitude parameters.",
#             ge=0.0,
#             le=180.0,
#             examples=5.1,
#         ),
#     ] = None
    level: Annotated[
        StationLevel,
        Field(
            description="Specify the level of detail for the results",
        ),
    ] = "station"
    includerestricted: Annotated[
        bool,
        Field(
            description="Specify if results should include information for restricted stations.",
        ),
    ] = False
    includeavailability: Annotated[
        bool,
        Field(
            description="Specify if results should include information about time series data availability.",
        ),
    ] = False
    nodata: Annotated[
        NoData,
        Field(
            description="Select status code for “no data”, either 204 (default) or 404"
        ),
    ] = '204'
    format: Annotated[
        StationFormat,
        Field(
            description=(
                "Specify format of result, either xml (default, StationXML, not yet implemented), "
                "text (defined in the FDSN specification, not yet implemented), or css (flatfile Site table rows)."
            )
        ),
    ] = "xml"
    asquery: Annotated[
        bool,
        Field(
            description="Debug your inputs by returning the database query instead of the normal output."
        ),
    ] = False

    model_config = ConfigDict(extra='ignore')
