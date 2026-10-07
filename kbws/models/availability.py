from enum import Enum
from textwrap import dedent
from typing import Annotated, Literal
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict, Field

from .common import NoData, Quality


class AvailabilityExtent(BaseModel):
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
            examples="IU",
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
    # quality: Annotated[
    #     Quality,
    #     Field(
    #         description="Select a specific SEED quality indicator, handling is data center dependent.",
    #     ),
    # ] = "B"
    merge: Annotated[
        Literal["samplerate", "quality", "overlap"], # this is so much easier than Enum. downsides?
        Field(
            description=dedent(
                """\
                If set to one of the following values, time spans are merged as described.

                `samplerate`: time spans from data with differing sample rates will be grouped together.
                If specified this field will be omitted from the result.

                `quality`: time spans from data with differing quality codes will be grouped together.
                If specified this field will be omitted from the result.

                `overlap`: time spans from data that overlap will be merged together.
                This option does not apply to the extent method.
                """
            ),
        ),
    ] = "samplerate"
    format: Annotated[
        Literal["text", "request"],
        Field(
            description=(
                "Specify format of result. (not yet implemented) "
            ),
        ),
    ] = "text"
    nodata: Annotated[
        NoData,
        Field(
            description="Select status code for “no data”, either 204 (default) or 404"
        ),
    ] = '204'


# all the same params as extent, plus two others
class AvailabilityQuery(AvailabilityExtent):
    mergegaps: Annotated[
        float,
        Field(
            description="If set, merge time spans that are separated by the specified tolerance in seconds.",
        ),
    ] = 0.0
    # show: Annotated[
    #     str,
    #     Field(
    #         description=(
    #             "If set to latestupdate, the latest times at which data contributing to the returned "
    #             "time spans were loaded into the repository are included in the result. "
    #             "This option applies to all formats except request"
    #         ),
    #     ),
    # ] = ...
