""" Utilities in support of FDSN formats.

"""
import io
import json
import os
from collections import namedtuple
from collections.abc import Iterable
from zipfile import ZipFile

from obspy import Catalog, Stream, UTCDateTime
from obspy.io.json.default import Default
from obspy.io.quakeml.core import Pickler  # for QuakeML string


def catalog_xml(catalog: Catalog) -> str:
    # TODO: make a PR to ObsPy to allow cat.write(format='QUAKEML') return the string version of quakeml
    # this logic is currently stolen from obspy.io.quakeml.core._write_quakeml
    nsmap_ = getattr(catalog, "nsmap", {})
    xml_doc = Pickler(nsmap=nsmap_).dumps(catalog)

    return xml_doc


def catalog_json(catalog: Catalog) -> str:
    default = Default(omit_nulls=False)
    return str(json.dumps(catalog, default=default, indent=2))


def event_text(catalog: Catalog) -> str:
    """Serialize an ObsPy Catalog using the FDSN event text format."""
    header = (
        "#EventID|Time|Latitude|Longitude|Depth/km|Author|Catalog|Contributor|"
        "ContributorID|MagType|Magnitude|MagAuthor|EventLocationName|EventType"
    )
    lines = [header]
    for event in catalog:
        origin = event.preferred_origin() or (event.origins[0] if event.origins else None)
        magnitude = event.preferred_magnitude() or (event.magnitudes[0] if event.magnitudes else None)
        creation_info = getattr(origin, "creation_info", None)
        event_creation_info = getattr(event, "creation_info", None)
        magnitude_info = getattr(magnitude, "creation_info", None)
        description = event.event_descriptions[0].text if event.event_descriptions else None
        values = [
            str(event.resource_id) if event.resource_id else None,
            origin.time if origin else None,
            origin.latitude if origin else None,
            origin.longitude if origin else None,
            origin.depth / 1000 if origin and origin.depth is not None else None,
            getattr(creation_info, "author", None)
            or getattr(event_creation_info, "author", None),
            None,
            None,
            None,
            magnitude.magnitude_type if magnitude else None,
            magnitude.mag if magnitude else None,
            getattr(magnitude_info, "author", None),
            description,
            event.event_type,
        ]
        lines.append("|".join(str(value) if value is not None else "" for value in values))
    return "\n".join(lines) + "\n"


def availability_text(rows, *, extent: bool, show: str | None = None) -> str:
    if extent:
        header = (
            "#Network Station Location Channel Quality SampleRate Earliest "
            "Latest Updated TimeSpans Restriction"
        )
        fields = (
            "network", "station", "location", "channel", "quality", "samplerate",
            "earliest", "latest", "updated", "timespans", "restriction",
        )
    else:
        fields = [
            "network", "station", "location", "channel", "quality", "samplerate",
            "earliest", "latest",
        ]
        header = "#Network Station Location Channel Quality SampleRate Earliest Latest"
        if show == "latestupdate":
            fields.append("updated")
            header += " Updated"

    lines = [header]
    for row in rows:
        values = []
        for field in fields:
            value = getattr(row, field, "-")
            if field in {"earliest", "latest", "updated"} and value not in (None, "-"):
                value = str(UTCDateTime(value))
            values.append(str(value if value is not None else "-"))
        lines.append(" ".join(values))
    return "\n".join(lines) + "\n"


def availability_json(rows, *, extent: bool, show: str | None = None) -> str:
    if extent:
        fields = (
            "network", "station", "location", "channel", "quality", "samplerate",
            "earliest", "latest", "updated", "timespans", "restriction",
        )
    else:
        fields = [
            "network", "station", "location", "channel", "quality", "samplerate",
            "earliest", "latest",
        ]
        if show == "latestupdate":
            fields.append("updated")

    output = []
    for row in rows:
        item = {}
        for field in fields:
            value = getattr(row, field, None)
            if field in {"earliest", "latest", "updated"} and value is not None:
                value = str(UTCDateTime(value))
            item[field] = value
        output.append(item)
    return json.dumps(output, indent=2)


def station_xml_bytes(inventory) -> bytes:
    """Serialize an ObsPy Inventory to StationXML bytes."""
    with io.BytesIO() as fp:
        inventory.write(fp, format="STATIONXML")
        return fp.getvalue()


def station_text(inventory, level: str) -> str:
    """Serialize an ObsPy Inventory using the FDSN station text format."""
    if level == "network":
        header = "#Network|Description|StartTime|EndTime|TotalStations"
        rows = inventory.networks
    elif level == "station":
        header = "#Network|Station|Latitude|Longitude|Elevation|SiteName|StartTime|EndTime"
        rows = ((network, station) for network in inventory.networks for station in network.stations)
    else:
        header = (
            "#Network|Station|Location|Channel|Latitude|Longitude|Elevation|Depth|Azimuth|Dip|"
            "SensorDescription|Scale|ScaleFrequency|ScaleUnits|SampleRate|StartTime|EndTime"
        )
        rows = (
            (network, station, channel)
            for network in inventory.networks
            for station in network.stations
            for channel in station.channels
        )

    lines = [header]
    for row in rows:
        if level == "network":
            values = [row.code, row.description, "", "", len(row.stations)]
        elif level == "station":
            network, station = row
            values = [
                network.code, station.code, station.latitude, station.longitude,
                station.elevation, station.site.name, station.start_date, station.end_date,
            ]
        else:
            network, station, channel = row
            sensitivity = getattr(
                getattr(channel, "response", None),
                "instrument_sensitivity",
                None,
            )
            values = [
                network.code, station.code, channel.location_code, channel.code,
                channel.latitude, channel.longitude, channel.elevation, channel.depth,
                channel.azimuth, channel.dip, getattr(channel.sensor, "type", None),
                getattr(sensitivity, "value", None),
                getattr(sensitivity, "frequency", None),
                getattr(sensitivity, "output_units", None),
                channel.sample_rate, channel.start_date, channel.end_date,
            ]
        lines.append("|".join(str(value if value is not None else "") for value in values))
    return "\n".join(lines) + "\n"


def availability_request(rows) -> str:
    lines = [
        " ".join((
            row.network,
            row.station,
            row.location,
            row.channel,
            str(UTCDateTime(row.earliest)),
            str(UTCDateTime(row.latest)),
        ))
        for row in rows
    ]
    return "\n".join(lines) + "\n"


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
            tr.write(fp, format="MSEED")
        fp.seek(0)
        byts = fp.read()

    return byts


def saczip_bytes(stream: Stream) -> bytes:
    """Produce an in-memory zip archive of sac files from _a Stream object.

    Names the files inside the archive following the IRIS FDSN-WS convention,
    with SAC traces named according to trace ID and first sample time, like:

        <archive_name>
            NETWORK.STATION.LOCATION.CHANNEL.QUALITY.YYYY.JJJ.HHMMSS.SAC

    Example:

        fdsnws-dataselect_2023-04-24t19 01 31z.sac.zip (request time)
            IU.TUC.00.BHZ.M.2010.058.063000.SAC (first sample time)

    Returns
    -------
    bytes

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

    Output looks like:

        ({'level': 'channel', 'format': 'text'},
         [['TA', 'A25A', '--', 'BH?', '2010-03-25T00:00:00', '2010-04-01T00:00:00'],
          ['IU', 'ANMO', '*', 'BH?', '2010-03-25T00:00:00', '2010-04-01T00:00:00'],
          ['IU', 'ANMO', '10', 'HHZ', '2010-03-25T00:00:00', '2010-04-01T00:00:00'],
          ['II', 'KURK', '00', 'BH?', '2010-03-25T00:00:00', '2010-04-01T00:00:00']])

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
