import json
import textwrap

from fastapi.testclient import TestClient
from obspy import read, Stream

from pisces.fdsn import Client
from pisces.tables.kbcore import Affiliation, Wfdisc
from pisces.util import literal_sql

import pytest

from kbws.formats import (
    saczip_bytes,
    mseed_bytes,

)
from kbws.main import app

ENDPOINT = "/fdsnws/dataselect/1/query?"

client = TestClient(app)

st = read()

# ----------------------------------------------
# fixtures the patch pisces.fdsn.Client.get_waveforms #####
@pytest.fixture(scope='function')
def get_waveforms_stream(monkeypatch):
    """ Patch pisces.fdsn.Client.get_waveforms to always return ObsPy's example Stream.
    """
    def mock_get_waveforms(*args, **kwargs):
        return st

    # replace Client.get_events with the mock
    monkeypatch.setattr(Client, 'get_waveforms', mock_get_waveforms)

@pytest.fixture(scope='function')
def get_waveforms_empty(monkeypatch):
    """ Return an empty Stream.
    """
    def mock_get_waveforms(*args, **kwargs):
        return Stream()

    # replace Client.get_events with the mock
    monkeypatch.setattr(Client, 'get_waveforms', mock_get_waveforms)

@pytest.fixture(scope='function')
def get_waveforms_query(monkeypatch, db_session):
    """ Return an Affiliation-Wfdisc joined SQLAlchemy query
    """
    def mock_get_waveforms(*args, **kwargs):
        return db_session.query(Affiliation, Wfdisc).filter(Affiliation.sta == Wfdisc.sta)

    # replace Client.get_events with the mock
    monkeypatch.setattr(Client, 'get_waveforms', mock_get_waveforms)


# ----------------------------------------------
# actual tests
def test_dataselect_format_miniseed(get_waveforms_stream):
    """ Test for proper miniseed response.
    """
    byts = mseed_bytes(st)
    response = client.get(
        (
            f"{ENDPOINT}"
            "starttime=2009-05-01T06:30:12.345&endtime=2009-05-02T06:30:12.345"
            "&network=IU&station=ANMO&location=--&channel=BHZ"
            "&format=miniseed"
        )
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/vnd.fdsn.mseed'
    assert response.content == byts


def test_dataselect_format_saczip(get_waveforms_stream):
    """ Test for proper SAC zip response. """
    byts = saczip_bytes(st)

    response = client.get(
        (
            f"{ENDPOINT}"
            "starttime=2009-05-01T06:30:12.345&endtime=2009-05-02T06:30:12.345"
            "&network=IU&station=ANMO&location=--&channel=BHZ"
            "&format=sac.zip"
        )
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'application/zip'
    assert response.content == byts


def test_dataselect_format_sql(get_waveforms_query, db_session):
    """ Test for proper SQL response. """
    sql = literal_sql(
        db_session.query(Affiliation, Wfdisc).filter(Affiliation.sta == Wfdisc.sta)
    )
    response = client.get(
        (
            f"{ENDPOINT}"
            "starttime=2009-05-01T06:30:12.345&endtime=2009-05-02T06:30:12.345"
            "&network=IU&station=ANMO&location=--&channel=BHZ"
            "&format=sql"
        )
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
    assert response.content == sql.encode('utf-8')


def test_dataselect_format_css(get_waveforms_query, db_session):
    """ Test for proper CSS Wfdisc flat file response. """
    anmo = Wfdisc(sta='ANMO', wfid=1)
    iu = Affiliation(sta='ANMO', net='IU')
    db_session.add_all([anmo, iu])
    db_session.commit()

    response = client.get(
        (
            f"{ENDPOINT}"
            "starttime=2009-05-01T06:30:12.345&endtime=2009-05-02T06:30:12.345"
            "&network=IU&station=ANMO&location=--&channel=BHZ"
            "&format=css"
        )
    )
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
    assert response.content == str(anmo).encode('utf-8')


def test_dataselect_bad_inputs():
    """ Test for bad inputs. """
    # nonexistant format
    response = client.get(
        (
            f"{ENDPOINT}"
            "starttime=2009-05-01T06:30:12.345&endtime=2009-05-02T06:30:12.345"
            "&network=IU&station=ANMO&location=--&channel=BHZ"
            "&format=bad"
        )
    )
    assert response.status_code == 400
    assert "Input should be 'miniseed', 'sac.zip', 'sql' or 'css'" in response.content.decode("utf-8")

    # misspelled starttime
    response = client.get(
        (
            f"{ENDPOINT}"
            "startime=2009-05-01T06:30:12.345&endtime=2009-05-02T06:30:12.345"
            "&network=IU&station=ANMO&location=--&channel=BHZ"
        )
    )
    assert response.status_code == 400


def test_dataselect_nodata(get_waveforms_empty):
    """ Test for empty results. """
    # default nodata value
    response = client.get(
        (
            f"{ENDPOINT}"
            "starttime=2009-05-01T06:30:12.345&endtime=2009-05-02T06:30:12.345"
            "&network=IU&station=ANMO&location=--&channel=BHZ"
        )
    )
    assert response.status_code == 204

    # user-supplied nodata value
    response = client.get(
        (
            f"{ENDPOINT}"
            "starttime=2009-05-01T06:30:12.345&endtime=2009-05-02T06:30:12.345"
            "&network=IU&station=ANMO&location=--&channel=BHZ"
            "&nodata=404"
        )
    )
    assert response.status_code == 404


def test_dataselect_post(get_waveforms_stream):
    """ Test for correct POST parsing. """

    # request file on disk
    txt = textwrap.dedent(
        """\
        quality=M
        minimumlength=0.0
        longestonly=FALSE
        TA A25A -- BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
        IU ANMO * BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
        IU ANMO 10 HHZ 2010-03-25T00:00:00 2010-04-01T00:00:00
        II KURK 00 BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
        """
    )

    # patched fdsn client.get_waveforms returns one st for each bulk line
    out = st + st + st + st
    # expected = _stream_to_mseed_bytes(out)
    expected = mseed_bytes(out)

    response = client.post(
        f"{ENDPOINT}",
        content=txt,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}, #don't understand this content-type
        # headers={'Content-Type': 'text/plain'},
    )
    assert response.status_code == 200
    assert response.content == expected
    assert response.headers['Content-Type'] == 'application/vnd.fdsn.mseed'

    # extra parameters are ignored
    txt = textwrap.dedent(
        """\
        quality=M
        minimumlength=0.0
        longestonly=FALSE
        fake_header=never_heard_of_it
        TA A25A -- BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
        IU ANMO * BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
        IU ANMO 10 HHZ 2010-03-25T00:00:00 2010-04-01T00:00:00
        II KURK 00 BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
        """
    )
    response = client.post(
        f"{ENDPOINT}",
        content=txt,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        # headers={'Content-Type': 'text/plain'},
    )
    assert response.status_code == 200
    # assert response.status_code == 400
    # assert b"Extra inputs are not permitted" in response.content

    # bulk lines are required
    txt = textwrap.dedent(
        """\
        quality=M
        minimumlength=0.0
        longestonly=FALSE
        """
    )
    response = client.post(
        f"{ENDPOINT}",
        content=txt,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    assert response.status_code == 400

# TODO: test formatted error response bodies
