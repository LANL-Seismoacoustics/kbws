"""
Here live the simple Pydantic classes/models that handle input type validation/conversion at our API
endpoints. These classes are used in the endpoint function calling signature, and to autogenerate
the OpenAPI documentation. Examples and descriptions can live in these models.

The main goal of this module is to add annotations to our simple models, so that FastAPI can build
rich OpenAPI documentations and specification files for users.

Note, the language of FastAPI is JSON, so Pydantic "models" (classes) used at FastAPI endpoints are
meant to represent JSON data being sent/received at API endpoints. FDSN Web Services don't speak in
JSON, they speak in query parameters, text, XML, and binary data. As such, our "models" are
generally going to be very simple scalar objects, like enumerated floats. Further, since our outputs
aren't JSON, we don't use these models in the responses, as many FastAPI apps do.  Instead, we
create and return custom FastAPI responses directly.  Our FastAPI app is a bit more complex than a
"normal" JSON-based API as a result.

See also:
https://fastapi.tiangolo.com/tutorial/schema-extra-example/
https://docs.pydantic.dev/usage/schema/

"""
from .availability import AvailabilityExtent, AvailabilityQuery
from .dataselect import DataselectQuery
from .event import EventQuery
from .station import StationQuery
