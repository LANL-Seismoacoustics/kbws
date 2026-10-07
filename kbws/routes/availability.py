import logging
from typing import Annotated

from fastapi import APIRouter, Query, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session


from ..logging import get_logger
from .. import database as db
from ..models import AvailabilityExtent, AvailabilityQuery

VERSION = "1.0.0"
MAJOR_VERSION = VERSION.split(".")[0]

logger = get_logger(__name__)

# All subsequent routes originate at this path
router = APIRouter(prefix=f"/fdsnws/availability/{MAJOR_VERSION}", tags=['availability'])


@router.get("/version", response_class=PlainTextResponse)
def availability_version():
    return VERSION


@router.get("/extent")
def availability_extent(
    params: Annotated[AvailabilityExtent, Query()],
    session: Session = Depends(db.get_db)
):
    """Earlies and latest time series holdings

    ### Example

    [http://0.0.0.0:8000/fdsnws/availability/1/extent?channel=BH?&endtime=2010-03-28&location=--&network=TA&starttime=2010-03-25&station=A25A](http://0.0.0.0:8000/fdsnws/dataselect/1/query?channel=BH?&endtime=2010-03-28&location=--&network=TA&starttime=2010-03-25&station=A25A)

    """
    # see: https://stackoverflow.com/a/8120432/745557
    # https://medium.com/@akarshith98/how-to-merge-overlapping-date-ranges-in-sql-a-data-engineers-guide-d0522e1a12e0
    pass


@router.post("/extent")
def availability_extent_post(
    params: Annotated[AvailabilityExtent, Query()],
    session: Session = Depends(db.get_db)
):
    """Query URL builder

    ### Example

    Add POST file example here.

    """
    pass


@router.post("/query")
def availability_query_post(
    params: Annotated[AvailabilityQuery, Query()],
    session: Session = Depends(db.get_db)
):
    """Query URL builder

    ### Example

    Add POST file example here.

    """
    pass


@router.get("/query")
def availability_query(
    params: Annotated[AvailabilityQuery, Query()],
    session: Session = Depends(db.get_db)
):
    """Query URL builder

    ### Example

    [http://0.0.0.0:8000/fdsnws/availability/1/query?channel=BH?&endtime=2010-03-28&location=--&network=TA&starttime=2010-03-25&station=A25A](http://0.0.0.0:8000/fdsnws/dataselect/1/query?channel=BH?&endtime=2010-03-28&location=--&network=TA&starttime=2010-03-25&station=A25A)

    """
    pass
