
"""Define and validate NASA FIRMS source-file contracts."""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


ARCHIVE_HEADER = (
    "latitude",
    "longitude",
    "brightness",
    "scan",
    "track",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "bright_t31",
    "frp",
    "daynight",
    "type",
)

NRT_HEADER = (
    "latitude",
    "longitude",
    "brightness",
    "scan",
    "track",
    "acq_date",
    "acq_time",
    "satellite",
    "instrument",
    "confidence",
    "version",
    "bright_t31",
    "frp",
    "daynight",
)

REGION_SLUGS = frozenset({
    "angola",
    "brasil",
    "rdc",
    "zambia",
    "california",
    "espana",
    "indonesia",
    "australia",
})

FILENAME_PATTERN = re.compile(
    r"^(fire_archive|fire_nrt)_"
    r"(M-C61|SV-C2|J1V-C2|J2V-C2)_"
    r"(\d+)\.csv$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SourceContract:
    """Expected structure and identity of one FIRMS source file."""

    region_id: str
    sensor_folder: str
    sensor: str
    platform_group: str
    product_token: str
    collection: str
    processing_stream: str
    processing_provider: str
    expected_instrument: str
    expected_platforms: tuple[str, ...]
    expected_header: tuple[str, ...]
    filename_prefix: str
    source_id: str


FOLDER_CONTRACTS = {
    "_modis": {
        "sensor": "MODIS",
        "platform_group": "MODIS",
        "product_token": "M-C61",
        "collection": "MODIS_C61",
        "expected_instrument": "MODIS",
        "expected_platforms": ("TERRA", "AQUA"),
    },
    "_viirs_snpp": {
        "sensor": "VIIRS",
        "platform_group": "SNPP",
        "product_token": "SV-C2",
        "collection": "VIIRS_C2",
        "expected_instrument": "SNPP",
        "expected_platforms": ("SNPP",),
    },
    "_viirs_20": {
        "sensor": "VIIRS",
        "platform_group": "NOAA-20",
        "product_token": "J1V-C2",
        "collection": "VIIRS_C2",
        "expected_instrument": "VIIRS",
        "expected_platforms": ("NOAA-20",),
    },
    "_viirs_21": {
        "sensor": "VIIRS",
        "platform_group": "NOAA-21",
        "product_token": "J2V-C2",
        "collection": "VIIRS_C2",
        "expected_instrument": "VIIRS",
        "expected_platforms": ("NOAA-21",),
    },
}

SATELLITE_TO_PLATFORM = {
    "TERRA": "TERRA",
    "AQUA": "AQUA",
    "SNPP": "SNPP",
    "N20": "NOAA-20",
    "N21": "NOAA-21",
}


def identify_source_contract(file_path: Path) -> SourceContract:
    """
    Identify the source contract using the folder and filename.

    The folder identifies the study region and sensor/platform.
    The filename identifies the processing stream and product.
    """

    file_path = Path(file_path)

    folder_name = file_path.parent.name.lower()
    filename = file_path.name

    matching_suffix = None
    folder_config = None

    # The longer suffixes are checked before shorter ones.
    for suffix in (
        "_viirs_snpp",
        "_viirs_20",
        "_viirs_21",
        "_modis",
    ):
        if folder_name.endswith(suffix):
            matching_suffix = suffix
            folder_config = FOLDER_CONTRACTS[suffix]
            break

    if matching_suffix is None or folder_config is None:
        raise ValueError(
            f"Unrecognised sensor folder: {folder_name}"
        )

    region_id = folder_name[:-len(matching_suffix)]

    if region_id not in REGION_SLUGS:
        raise ValueError(
            f"Unrecognised study region in folder: {folder_name}"
        )

    match = FILENAME_PATTERN.fullmatch(filename)

    if match is None:
        raise ValueError(
            f"Unrecognised FIRMS filename: {filename}"
        )

    filename_prefix, product_token, source_id = match.groups()

    if product_token.upper() != folder_config["product_token"]:
        raise ValueError(
            f"Product token {product_token!r} does not match "
            f"sensor folder {folder_name!r}"
        )

    processing_stream = (
        "ARCHIVE"
        if filename_prefix.lower() == "fire_archive"
        else "NRT"
    )

    expected_header = (
        ARCHIVE_HEADER
        if processing_stream == "ARCHIVE"
        else NRT_HEADER
    )

    processing_provider = (
        "UNIVERSITY_OF_MARYLAND"
        if processing_stream == "ARCHIVE"
        else "NASA_LANCE_FIRMS"
    )

    return SourceContract(
        region_id=region_id,
        sensor=folder_config["sensor"],
        sensor_folder=folder_name,
        platform_group=folder_config["platform_group"],
        product_token=folder_config["product_token"],
        collection=folder_config["collection"],
        processing_stream=processing_stream,
        processing_provider=processing_provider,
        expected_instrument=folder_config["expected_instrument"],
        expected_platforms=folder_config["expected_platforms"],
        expected_header=expected_header,
        filename_prefix=filename_prefix.lower(),
        source_id=source_id,
    )


def read_source_header(file_path: Path) -> tuple[str, ...]:
    """Read a CSV header and reject empty or duplicated headers."""

    file_path = Path(file_path)

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.reader(csv_file)

        try:
            header = tuple(next(reader))
        except StopIteration:
            raise ValueError(
                f"CSV file is empty: {file_path}"
            ) from None

    if not header:
        raise ValueError(
            f"CSV file has an empty header: {file_path}"
        )

    if len(header) != len(set(header)):
        raise ValueError(
            f"CSV file contains duplicate column names: {file_path}"
        )

    return header


def validate_source_header(
    file_path: Path,
    contract: SourceContract | None = None,
) -> tuple[str, ...]:
    """
    Validate a file's exact header against its source contract.

    When no contract is provided, it is identified from the file path.
    Returns the actual header if validation succeeds.
    Raises ValueError if the header is unexpected.
    """

    file_path = Path(file_path)

    if contract is None:
        contract = identify_source_contract(file_path)

    actual_header = read_source_header(file_path)

    if actual_header != contract.expected_header:
        raise ValueError(
            f"Header mismatch in {file_path.name}. "
            f"Expected {contract.expected_header}, "
            f"received {actual_header}."
        )

    return actual_header


def identify_platform(satellite_raw: str | None) -> str:
    """Map a raw FIRMS satellite identifier to its canonical platform."""

    if satellite_raw is None:
        raise ValueError("Missing satellite identifier")

    satellite = satellite_raw.strip().upper()

    if not satellite:
        raise ValueError("Missing satellite identifier")

    try:
        return SATELLITE_TO_PLATFORM[satellite]
    except KeyError:
        raise ValueError(
            f"Unknown satellite identifier: {satellite_raw!r}"
        ) from None


def validate_source_identity(
    contract: SourceContract,
    satellite_raw: str | None,
    instrument_raw: str | None,
) -> str:
    """
    Validate row-level satellite and instrument identity.

    Returns the canonical platform:
    TERRA, AQUA, SNPP, NOAA-20 or NOAA-21.

    Raises ValueError if the row does not match its source contract.
    """

    if satellite_raw is None or not satellite_raw.strip():
        raise ValueError("Missing satellite identifier")

    if instrument_raw is None or not instrument_raw.strip():
        raise ValueError("Missing instrument identifier")

    platform = identify_platform(satellite_raw)
    instrument = instrument_raw.strip().upper()

    if platform not in contract.expected_platforms:
        raise ValueError(
            f"Platform {platform!r} is inconsistent with "
            f"source platform group {contract.platform_group!r}"
        )

    if instrument != contract.expected_instrument:
        raise ValueError(
            f"Instrument {instrument!r} is inconsistent with "
            f"expected instrument {contract.expected_instrument!r}"
        )

    return platform
