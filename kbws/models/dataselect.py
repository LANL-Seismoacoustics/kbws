""" Models for the dataselect API endpoint.
"""
from enum import Enum
from typing import Annotated
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field

from .common import NoData, Quality


class DataselectFormat(str, Enum):
    miniseed = "miniseed"
    sac = "sac.zip"
    sql = "sql"
    css = "css"



class DataselectQuery(BaseModel):
    model_config = ConfigDict(extra='ignore')

    starttime: Annotated[
        datetime | date,
        Field(
            description=(
                "Limit results to time series samples on or after the specified start time, "
                "using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]"
            ),
            examples="2009-05-01T06:30:00.000",
        ),
    ]
    endtime: Annotated[
        datetime | date,
        Field(
            description=(
                "Limit results to time series samples on or before the specified end time, "
                "using ISO8601 format YYYY-MM-DDThh:mm:ss[.ssssss]"
            ),
            examples="2009-06-01T10:30:00.000",
        ),
    ]
    network: Annotated[
        str,
        Field(
            description=(
                "Select one or more network codes. Can be SEED network codes or data center "
                "defined codes. Multiple codes are comma-separated"
            ),
            examples=["IU"],
        ),
    ]
    station: Annotated[
        str,
        Field(
            description="Select one or more SEED station codes. Multiple codes are comma-separated",
            examples="ANMO",
        ),
    ]
    location: Annotated[
        str,
        Field(
            description="Select one or more SEED location identifiers. Multiple identifiers are comma-separated. As a special case ‘--’ (two dashes) will be translated to a string of two space characters to match blank location IDs.",
            examples="00",
        ),
    ] = ...
    channel: Annotated[
        str,
        Field(
            description="Select one or more SEED channel codes. Multiple codes are comma-separated.",
            examples="BH1",
        ),
    ] = ...
#     quality: Annotated[
#         Quality,
#         Field(
#             description="Select a specific SEED quality indicator, handling is data center dependent.",
#         ),
#     ] = "B"
#     minimumlength: Annotated[
#         float,
#         Field(
#             description="Limit results to continuous data segments of a minimum length specified in seconds.",
#             ge=0.0,
#             include_in_schema=False,
#         ),
#     ] = 0.0
#     longestonly: Annotated[
#         bool,
#         Field(
#             description="Limit results to the longest continuous segment per channel.",
#             include_in_schema=False,
#         ),
#     ] = False
    format: Annotated[
        DataselectFormat,
        Field(
            description=(
                "Specify format of result: miniseed (default), text (described in FDSN specification, not yet implemented), "
                "css (text Wfdisc table rows), or sql (the SQL query that was built, not the results)."
            ),
        ),
    ] = DataselectFormat.miniseed
    nodata: Annotated[
        NoData,
        Field(
            description="Select status code for “no data”, either 204 (default) or 404"
        ),
    ] = '204'
