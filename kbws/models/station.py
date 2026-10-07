""" Models for the station API endpoint.
"""
from enum import Enum
from typing import Annotated, Union
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict
from fastapi import Query

from .common import NoData

class StationFormat(str, Enum):
    xml = "xml"
    css = "css"
    test = "text"

class StationLevel(str, Enum):
    network = "network"
    station = "station"
    channel = "channel"
    respones = "response"

class StationQuery(BaseModel):
    starttime: Annotated[
        Union[datetime, date] | None,
        Query(
            default=...,  # '...' for the default value means that it's required
            description="Limit results to channels operating on or after the specified start time, using ISO8601 format jYYYY-MM-DDThh:mm:ss[.ssssss]",
            examples="2012-11-01T00:00:00.000",
        ),
    ] = None
    endtime: Annotated[
        Union[datetime, date] | None,
        Query(
            description="Limit results to channels operating on or before the specified end time, using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]",
            examples="2012-11-03",
        ),
    ] = None
    # startbefore: Annotated[
    #     Union[datetime, date] | None,
    #     Query(
    #         description="Limit to metadata epochs starting before specified time. Applied to channel epochs, using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]",
    #         examples="2012-11-03",
    #     ),
    # ] = None
    # startafter: Annotated[
    #     Union[datetime, date] | None,
    #     Query(
    #         description="Limit to metadata epochs starting after specified time. Applied to channel epochs, using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]",
    #         examples="2012-11-03",
    #     ),
    # ] = None
    # endbefore: Annotated[
    #     Union[datetime, date] | None,
    #     Query(
    #         description="Limit to metadata epochs ending before specified time. Applied to channel epochs, using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]",
    #         examples="2012-11-03",
    #     ),
    # ] = None
    # endafter: Annotated[
    #     Union[datetime, date] | None,
    #     Query(
    #         description="Limit to metadata epochs ending after specified time. Applied to channel epochs, using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]",
    #         examples="2012-11-03",
    #     ),
    # ] = None
    network: Annotated[
        str,
        Query(
            description="Select one or more network codes. Can be SEED network codes or data center defined codes. Multiple codes are comma-separated",
            examples="IU",
        ),
    ] = ...
    station: Annotated[
        str,
        Query(
            description="Select one or more SEED station codes. Multiple codes are comma-separated",
            examples="ANMO",
        ),
    ] = ...
#     location: Annotated[
#         str,
#         Query(
#             description="Select one or more SEED location identifiers. Multiple identifiers are comma-separated. As a special case ‘--’ (two dashes) will be translated to a string of two space characters to match blank location IDs.",
#             examples="00",
#         ),
#     ] = ...
    channel: Annotated[
        str,
        Query(
            description="Select one or more SEED channel codes. Multiple codes are comma-separated.",
            examples="BH1",
        ),
    ] = ...
    minlatitude: Annotated[
        float | None,
        Query(
            description="Limit to stations with a latitude larger than or equal to the specified minimum.",
            ge=-90.0,
            le=90.0,
            examples=40.1,
        ),
    ] = None
    maxlatitude: Annotated[
        float | None,
        Query(
            description="Limit to stations with a latitude smaller than or equal to the specified maximum.",
            ge=-90.0,
            le=90.0,
            examples=46.9,
        ),
    ] = None
    minlongitude: Annotated[
        float | None,
        Query(
            description="Limit to stations with a longitude larger than or equal to the specified minimum.",
            ge=-180.0,
            le=180.0,
            examples=-10.5,
        ),
    ] = None
    maxlongitude: Annotated[
        float | None,
        Query(
            description="Limit to stations with a longitude smaller than or equal to the specified maximum.",
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
#             example=5.1,
#         ),
#     ] = 0
    level: Annotated[
        StationLevel,
        Query(
            description="Specify the level of detail for the results",
        ),
    ] = "station"
    includerestricted: Annotated[
        bool,
        Query(
            description="Specify if results should include information for restricted stations."
        ),
    ] = False
    includeavailability: Annotated[
        bool,
        Query(
            description="Specify if results should include information about time series data availability."
        ),
    ] = False
    nodata: Annotated[
        NoData,
        Query(
            description="Select status code for “no data”, either 204 (default) or 404"
        ),
    ] = '204'
    format: Annotated[
        str,
        Query(
            description="Specify format of result, either xml (default, not yet implemented), text (defined below, not yet implemented), or css (flatfile Site table rows). If this parameter is not specified the service must return StationML."
        ),
    ] = "xml"
    asquery: Annotated[
        bool,
        Query(
            description="Debug your inputs by returning the database query instead of the normal output."
        ),
    ] = False

    model_config = ConfigDict(extra='ignore')
