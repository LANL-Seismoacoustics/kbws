""" Utilities in support of FDSN formats.

"""
from collections import namedtuple
import io
import json
import os
from typing import Iterable
from zipfile import ZipFile

from obspy import Stream, Catalog
from obspy.io.quakeml.core import Pickler # for QuakeML string
from obspy.io.json.default import Default

def catalog_xml(catalog: Catalog) -> str:
    # TODO: make a PR to ObsPy to allow cat.write(format='QUAKEML') return the string version of quakeml
    # this logic is currently stolen from obspy.io.quakeml.core._write_quakeml
    nsmap_ = getattr(catalog, "nsmap", {})
    xml_doc = Pickler(nsmap=nsmap_).dumps(catalog)

    return xml_doc


def catalog_json(catalog: Catalog) -> str:
    default = Default(omit_nulls=False)
    return str(json.dumps(catalog, default=default, indent=2))



def mseed_bytes(stream: Stream) -> bytes:
    """Produce an in-memory miniSEED archive from a Stream object.

    Returns
    -------
    bytes

    Notes
    -----
    This may start to fail with large requests, as both the Stream and the output
    bytes will be in-memory during the lifetime of the request.

    """
    with io.BytesIO() as fp:
        for tr in stream:
            (type(tr))
            tr.write(fp, format="MSEED")
        fp.seek(0)
        byts = fp.read()

    return byts


def saczip_bytes(stream: Stream) -> bytes:
    """Produce an in-memory zip archive of sac files from _a Stream object.

    Names the files inside the archive following the IRIS FDSN-WS convention,
    with SAC traces named according to trace ID, request quality, and first sample time, like:
    <archive_name>
        NETWORK.STATION.LOCATION.CHANNEL.QUALITY.YYYY.JJJ.HHMMSS.SAC

    Returns
    -------
    bytes

    Example
    -------
    fdsnws-dataselect_2023-04-24t19 01 31z.sac.zip (request time)
        IU.TUC.00.BHZ.M.2010.058.063000.SAC (first sample time)

    Notes
    -----
    This may start to fail with large requests, as both the Stream and the output
    bytes will be in-memory during the lifetime of the request.

    """
    with io.BytesIO() as fp:
        with ZipFile(fp, "w") as zipfp:
            for tr in stream:
                first_sample_time = tr.stats.starttime.strftime("%Y.%j.%H%M%S")
                sacname = f"{tr.id}.{first_sample_time}.SAC"
                with zipfp.open(sacname, "w") as sacfp:
                    tr.write(sacfp, format="SAC")
        fp.seek(0)
        byts = fp.read()

    return byts


WaveformFormat = namedtuple(
    "WaveformFormat", ["name", "obspy_format", "mimetype", "extension", "convert_stream"]
)

miniseed = WaveformFormat(
    name="miniseed",
    obspy_format="MSEED",
    mimetype="application/vnd.fdsn.mseed",
    extension="mseed",
    convert_stream=mseed_bytes,
)
saczip = WaveformFormat(
    name="sac.zip",
    obspy_format="SAC",
    mimetype="application/zip",
    extension="sac.zip",
    convert_stream=saczip_bytes,
)
WAVEFORM_FORMATS = {fmt.name: fmt for fmt in [miniseed, saczip]}


# def post_format(body: Iterable[str]):
def post_parse(body: Iterable[str]):
    """
    Params
    ------
    body
        Lines of a station POST query.

    Returns
    -------
    params : dict[str, str]
        string keys, string values
    bulk : list[list[str]]
        network, station, location, channel, starttime, endtime

    Raises
    ------
    ValueError
        bulk lines don't have the right number of values in a line

    Notes
    -----
    POST looks like this:

    level=channel
    format=text
    TA A25A -- BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
    IU ANMO * BH? 2010-03-25T00:00:00 2010-04-01T00:00:00
    IU ANMO 10 HHZ 2010-03-25T00:00:00 2010-04-01T00:00:00
    II KURK 00 BH? 2010-03-25T00:00:00 2010-04-01T00:00:00

    Output looks like this:
    (
        {'level': 'channel', 'format': 'text'},
        [
            ['TA', 'A25A', '--', 'BH?', '2010-03-25T00:00:00', '2010-04-01T00:00:00'],
            ['IU', 'ANMO', '*', 'BH?', '2010-03-25T00:00:00', '2010-04-01T00:00:00'],
            ['IU', 'ANMO', '10', 'HHZ', '2010-03-25T00:00:00', '2010-04-01T00:00:00'],
            ['II', 'KURK', '00', 'BH?', '2010-03-25T00:00:00', '2010-04-01T00:00:00']
        ]
    )

    """
    params = {}
    bulk = []
    for line in body:
        if '=' in line:
            key, val = line.split('=')
            params[key] = val
        else:
            net, sta, loc, chan, starttime, endtime = line.split()
            bulk.append([net, sta, loc, chan, starttime, endtime])

    # empty dict, list if none were provided
    return params, bulk


def post_format(params, bulk):
    """ The opposite of post_parse.
    """
    param_lines =  [
        f"{key}={value}" for key, value in params.items()
    ]
    bulk_lines = [
        " ".join(line) for line in bulk
    ]

    param_block = os.linesep.join(param_lines)
    bulk_block = os.linesep.join(bulk_lines)

    return param_block + os.linesep + bulk_block
