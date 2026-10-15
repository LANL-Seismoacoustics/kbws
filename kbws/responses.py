"""FDSN-WS standard error responses.

All FDSN error responses share one plain-text template (see the FDSN
Web Services Specification, "Error Handling"). Build one with
`fdsn_error_response`, passing the request and a `ResponseCode`.

Usage
-----
>>> from kbws.responses import fdsn_error_response, BAD_REQUEST
>>> return fdsn_error_response(request, BAD_REQUEST, detail=str(exc), service_version=VERSION)

"""
from dataclasses import dataclass
from textwrap import dedent

from fastapi import Request
from fastapi.responses import PlainTextResponse
from obspy import UTCDateTime


@dataclass(frozen=True)
class ResponseCode:
    """FDSN-WS standard response code and message."""
    code: int
    message: str


SUCCESS = ResponseCode(200, 'Successful request.')
NO_DATA = ResponseCode(204, 'No data matches the selection.')
BAD_REQUEST = ResponseCode(400, 'Badly formed request.')
UNAUTHORIZED = ResponseCode(401, 'Unauthorized, authentication required.')
AUTH_FAILED = ResponseCode(403, 'Authentication failed or access blocked to restricted data.')
NO_DATA_ALT = ResponseCode(404, NO_DATA.message)
REQUEST_TOO_LARGE = ResponseCode(413, 'Request or response too large.')
URL_TOO_LONG = ResponseCode(414, 'Request URI is too long.')
INTERNAL_ERROR = ResponseCode(500, 'Internal server error.')
TEMP_UNAVAILABLE = ResponseCode(503, 'Service temporarily unavailable.')

_TEMPLATE = dedent(
    """\
    ----------------------------------------------------
    Error {code}: {simple_descr}

    {detail}

    Usage details are available from {service_docs_uri}

    Request:
    {submitted_url}

    Request Submitted:
    {utc_date_time}

    Service version:
    {service_version}
    ----------------------------------------------------
    """
)


def fdsn_error_response(
    request: Request,
    response_code: ResponseCode,
    detail: str,
    service_version: str,
) -> PlainTextResponse:
    """Build the standard FDSN plain-text error response for `response_code`.

    Parameters
    ----------
    request : fastapi.Request
        Used to fill in the usage-docs URI and the submitted URL/query.
    response_code : ResponseCode
        One of the module-level constants, e.g. `BAD_REQUEST`, `NO_DATA_ALT`.
    detail : str
        Specific, request-dependent error detail (e.g. a validation message).
    service_version : str
        The version of the FDSN service that raised the error.

    """
    body = _TEMPLATE.format(
        code=response_code.code,
        simple_descr=response_code.message,
        detail=detail,
        service_docs_uri=request.base_url,
        submitted_url=str(request.url),
        utc_date_time=UTCDateTime(),
        service_version=service_version,
    )
    return PlainTextResponse(content=body, status_code=response_code.code)
