from dataclasses import dataclass, asdict
from textwrap import dedent

from obspy import UTCDateTime

from fastapi.responses import PlainTextResponse


@dataclass
class ResponseCode:
    """ FDSN-WS standard response codes and messages.

    Usage:
    """
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

@dataclass
class FDSNErrorText:
    """ Formattable error response text template

    Use like this:
    e = FDSNErrorText(
        error_code=REQUEST_TOO_LARGE.code,
        simple_descr=REQUEST_TOO_LARGE.message,
        ...
    )
    return PlainTextResponse(str(e), status_code=e.error_code)
    """
    error_code: int
    simple_descr: str
    detail: str
    service_docs_uri: str
    submitted_url: str
    utc_date_time: UTCDateTime
    service_version: str

    def __str__(self):
        txt = dedent(
            """\
            ----------------------------------------------------
            Error {error_code}: {simple_descr}

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
        ).format(**asdict(self))
        return txt

# TODO: override some FastAPI exceptions with our own.
# https://fastapi.tiangolo.com/tutorial/handling-errors/#override-request-validation-exceptions
# https://medium.com/@geetansh2k1/the-best-way-to-handle-exceptions-in-a-fastapi-application-37596995355c
# these follow: https://github.com/Kludex/starlette/blob/main/starlette/responses.py#L192
class FDSNErrorResponse(PlainTextResponse):
    """
    Usage
    -----
    >>> from kbws.responses import BAD_REQUEST, FDSNResponse
    >>> # inside endpoint function
    >>> try:
    ...     # do something
    ... except (whatever exception you're expecting) as e:
    ...     r = FDSNResponse(
    ...             str(e),
    ...             BAD_REQUEST.status_code,
    ...             BAD_REQUEST.simple_descr,
    ...             service_docs_uri=request.base_url,
    ...             submitted_url=request['path'],
    ...             utc_date_time=UTCDateTime(),
    ...             service_version=VERSION,
    ...     )
    ...     return r
    """
    def __init__(self,
        content,
        status_code,
        simple_descr,
        service_docs_url,
        submitted_url,
        service_version
    ):
        self.simple_descr = simple_descr
        self.service_docs_url = service_docs_url
        self.submitted_url = submitted_url
        self.service_version = service_version
        self.utc_date_time = UTCDateTime()

        super().__init__(content, status_code)

    def render(self, content):
        template = dedent(
            """\
            ----------------------------------------------------
            Error {resp.status_code}: {resp.simple_descr}

            {content}

            Usage details are available from {resp.service_docs_url}

            Request:
            {resp.submitted_url}

            Request Submitted:
            {resp.utc_date_time}

            Service version:
            {resp.service_version}
            ----------------------------------------------------
            """
        )
        body = template.format(
            resp=self,
            content=content,
        )
        return body.encode('utf-8')


class BadRequestResponse(FDSNErrorResponse):
    # accept params needed from the call site
    def __init__(self,
        content,
        service_docs_url,
        submitted_url,
        service_version
    ):
        # Pass those and BadRequestResponse-specific params to more parent/FDSNErrorResponse
        super().__init__(
            content,
            400,
            "Badly formed request.",
            service_docs_url,
            submitted_url,
            service_version
        )

class UnauthorizedResponse(FDSNErrorResponse):
    def __init__(self,
        content,
        service_docs_url,
        submitted_url,
        service_version
    ):
        super().__init__(
            content,
            401,
            'Unauthorized, authentication required.',
            service_docs_url,
            submitted_url,
            service_version
        )

class AuthFailedResponse(FDSNErrorResponse):
    def __init__(self,
        content,
        service_docs_url,
        submitted_url,
        service_version
    ):
        super().__init__(
            content,
            403,
            'Authentication failed or access blocked to restricted data.',
            service_docs_url,
            submitted_url,
            service_version
        )

class NoDataAltResponse(FDSNErrorResponse):
    def __init__(self,
        content,
        service_docs_url,
        submitted_url,
        service_version
    ):
        super().__init__(
            content,
            404,
            'No data matches the selection.',
            service_docs_url,
            submitted_url,
            service_version
        )

class RequestTooLargeResponse(FDSNErrorResponse):
    def __init__(self,
        content,
        service_docs_url,
        submitted_url,
        service_version
    ):
        super().__init__(
            content,
            413,
            'Request or response too large.',
            service_docs_url,
            submitted_url,
            service_version
        )

class URLTooLongResponse(FDSNErrorResponse):
    def __init__(self,
        content,
        service_docs_url,
        submitted_url,
        service_version
    ):
        super().__init__(
            content,
            414,
            'Request URI is too long.',
            service_docs_url,
            submitted_url,
            service_version
        )

class InternalErrorResponse(FDSNErrorResponse):
    def __init__(self,
        content,
        service_docs_url,
        submitted_url,
        service_version
    ):
        super().__init__(
            content,
            500,
            'Internal server error.',
            service_docs_url,
            submitted_url,
            service_version
        )

class TemporarilyUnavailableResponse(FDSNErrorResponse):
    def __init__(self,
        content,
        service_docs_url,
        submitted_url,
        service_version
    ):
        super().__init__(
            content,
            503,
            'Service temporarily unavailable.',
            service_docs_url,
            submitted_url,
            service_version
        )
