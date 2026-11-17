"""Request models for the FDSN availability service."""
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import NoData


AvailabilityFormat = Literal["text", "json", "request"]
OrderBy = Literal[
    "nslc_time_quality_samplerate",
    "latestupdate",
    "latestupdate_desc",
    "timespancount",
    "timespancount_desc",
]


class AvailabilityExtent(BaseModel):
    """FDSN availability parameters shared by ``query`` and ``extent``."""

    model_config = ConfigDict(extra="ignore")

    starttime: Annotated[
        datetime | date,
        Field(
            description="Limit results to samples on or after this UTC time.",
            examples="2009-05-01T06:30:00.000",
        ),
    ]
    endtime: Annotated[
        datetime | date,
        Field(
            description="Limit results to samples on or before this UTC time.",
            examples="2009-06-01T10:30:00.000",
        ),
    ]
    network: Annotated[
        str,
        Field(
            description="Network code or wildcard; comma-separated values are allowed.",
            examples="IU",
        ),
    ]
    station: Annotated[
        str,
        Field(
            description="Station code or wildcard; comma-separated values are allowed.",
            examples="ANMO",
        ),
    ]
    location: Annotated[
        str,
        Field(
            description=(
                "Location code or wildcard; comma-separated values are allowed. "
                "Not implemented yet and silently ignored."
            ),
            examples="00",
        ),
    ]
    channel: Annotated[
        str,
        Field(
            description="Channel code or wildcard; comma-separated values are allowed.",
            examples="BHZ",
        ),
    ]
    quality: Annotated[
        str | None,
        Field(
            description=(
                "Quality code or wildcard; support is data-center dependent. "
                "Not implemented yet and silently ignored."
            )
        ),
    ] = None
    merge: Annotated[
        str | None,
        Field(
            description=(
                "Comma-separated merge flags: samplerate, quality, and/or overlap. "
                "Quality and overlap merging are not implemented yet and silently ignored."
            ),
        ),
    ] = None
    orderby: Annotated[
        OrderBy,
        Field(
            description=(
                "Order in which availability rows are returned. "
                "Not implemented yet and silently ignored."
            )
        ),
    ] = "nslc_time_quality_samplerate"
    limit: Annotated[
        int | None,
        Field(
            ge=0,
            description=(
                "Maximum number of time spans to return. "
                "Not implemented yet and silently ignored."
            ),
        ),
    ] = None
    includerestricted: Annotated[
        bool,
        Field(description="Include restricted data when true."),
    ] = False
    format: Annotated[
        AvailabilityFormat,
        Field(description="Response format."),
    ] = "text"
    nodata: Annotated[
        NoData,
        Field(description="HTTP status for no matching data: 204 or 404."),
    ] = "204"


class AvailabilityQuery(AvailabilityExtent):
    """FDSN availability parameters for the ``query`` method."""

    mergegaps: Annotated[
        float,
        Field(
            ge=0.0,
            description="Merge spans separated by no more than this many seconds.",
        ),
    ] = 0.0
    show: Annotated[
        Literal["latestupdate"] | None,
        Field(
            description=(
                "Include the latest contributing update time."
            )
        ),
    ] = None
