
"""Validate raw NASA FIRMS MODIS and VIIRS observations.

Source-level contract failures raise ValueError.
Row-level validation errors make an observation invalid.
Quality flags describe anomalies without automatically invalidating it.
Raw source files are read only and are never modified.
"""

from __future__ import annotations

import csv
import math
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from collections.abc import Mapping

from dotenv import load_dotenv

from src.source_contracts import (
    identify_source_contract,
    validate_source_header,
    validate_source_identity,
)


NUMERIC_FIELDS = (
    "latitude",
    "longitude",
    "brightness",
    "scan",
    "track",
    "bright_t31",
    "frp",
)

ALLOWED_DAYNIGHT = frozenset({"D", "N"})
ALLOWED_VIIRS_CONFIDENCE = frozenset({"l", "n", "h"})
ALLOWED_DETECTION_TYPES = frozenset({"0", "1", "2", "3"})


def get_data_directory() -> Path:
    """Load and return the configured raw data directory."""

    load_dotenv()

    data_dir = os.getenv("SUTELLITE_DATA_DIR")

    if not data_dir:
        raise EnvironmentError(
            "SUTELLITE_DATA_DIR is not configured in the .env file."
        )

    path = Path(data_dir)

    if not path.exists():
        raise FileNotFoundError(
            f"Data directory not found: {path}"
        )

    if not path.is_dir():
        raise NotADirectoryError(
            f"Data path is not a directory: {path}"
        )

    return path


def validate_numeric_field(
    field: str,
    value: str | None,
) -> str | None:
    """Validate a numeric source field without changing its value.

    Negative FRP is deliberately not rejected here. It is retained and
    reported separately as a quality flag.
    """

    if value is None or str(value).strip() == "":
        return "missing"

    try:
        number = float(value)
    except (ValueError, TypeError):
        return "not_numeric"

    if not math.isfinite(number):
        return "not_finite"

    if field == "latitude" and not -90 <= number <= 90:
        return "out_of_range"

    if field == "longitude" and not -180 <= number <= 180:
        return "out_of_range"

    if field in {"scan", "track"} and number <= 0:
        return "out_of_range"

    return None


def validate_date(value: str | None) -> str | None:
    """Validate an acquisition date in YYYY-MM-DD format."""

    if value is None or not isinstance(value, str) or not value.strip():
        return "missing"

    value = value.strip()

    if (
        len(value) != 10
        or value[4] != "-"
        or value[7] != "-"
    ):
        return "invalid_date"

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return "invalid_date"

    return None


def validate_time(value: str | None) -> str | None:
    """Validate acquisition time in four-digit HHMM format."""

    if value is None or not isinstance(value, str) or not value.strip():
        return "missing"

    value = value.strip()

    if len(value) != 4 or not value.isdigit():
        return "invalid_time"

    hour = int(value[:2])
    minute = int(value[2:])

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return "invalid_time"

    return None


def validate_categorical_field(
    field: str,
    value: str | None,
    sensor: str,
) -> str | None:
    """Validate categorical fields using sensor-specific conventions."""

    if value is None or not isinstance(value, str) or not value.strip():
        return "missing"

    value = value.strip()
    sensor = sensor.upper()

    if field == "daynight":
        if value.upper() not in ALLOWED_DAYNIGHT:
            return "invalid_category"

    elif field == "confidence":
        if sensor == "MODIS":
            try:
                confidence = float(value)
            except ValueError:
                return "not_numeric"

            if (
                not math.isfinite(confidence)
                or not 0 <= confidence <= 100
            ):
                return "out_of_range"

        elif sensor == "VIIRS":
            if value.lower() not in ALLOWED_VIIRS_CONFIDENCE:
                return "invalid_category"

        else:
            return "unknown_sensor"

    elif field == "type":
        if value not in ALLOWED_DETECTION_TYPES:
            return "invalid_category"

    return None


def validate_row(
    row: Mapping[str, str | None],
    sensor: str,
) -> list[str]:
    """Validate observation fields and return row-level validation errors.

    File identity and source-schema validation are handled separately
    by the source-contract layer.
    """

    errors = []

    for field in NUMERIC_FIELDS:
        result = validate_numeric_field(field, row.get(field))

        if result:
            errors.append(f"{field}:{result}")

    result = validate_date(row.get("acq_date"))

    if result:
        errors.append(f"acq_date:{result}")

    result = validate_time(row.get("acq_time"))

    if result:
        errors.append(f"acq_time:{result}")

    for field in ("confidence", "daynight"):
        result = validate_categorical_field(
            field,
            row.get(field),
            sensor,
        )

        if result:
            errors.append(f"{field}:{result}")

    # ARCHIVE has a type column; NRT does not.
    if "type" in row:
        result = validate_categorical_field(
            "type",
            row.get("type"),
            sensor,
        )

        if result:
            errors.append(f"type:{result}")

    return errors


def get_row_quality_flags(
    row: Mapping[str, str | None],
) -> list[str]:
    """Return quality flags that do not automatically invalidate a row."""

    flags = []

    raw_frp = row.get("frp")

    if raw_frp is not None and raw_frp.strip():
        try:
            frp = float(raw_frp)
        except (ValueError, TypeError):
            frp = None

        if frp is not None and math.isfinite(frp) and frp < 0:
            flags.append("negative_frp")

    return flags


def _ensure_statistics(statistics: dict) -> None:
    """Initialise missing statistics fields without replacing existing data."""

    defaults = {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "files_processed": 0,
        "quality_flagged_rows": 0,
    }

    for key, value in defaults.items():
        statistics.setdefault(key, value)

    statistics.setdefault("errors", Counter())
    statistics.setdefault("quality_flags", Counter())
    statistics.setdefault("source_identity_errors", Counter())


def _is_malformed_row(row: dict) -> bool:
    """Detect rows with extra columns or missing trailing fields."""

    return (
        None in row
        or any(value is None for value in row.values())
    )


def process_file(file_path: Path, statistics: dict) -> None:
    """Validate a source CSV row by row using its exact source contract.

    Source-level failures (unsupported filename, inconsistent folder/token,
    or unexpected header) raise ValueError before observation processing.
    """

    file_path = Path(file_path)
    _ensure_statistics(statistics)

    # Identify and validate the source before reading observations.
    contract = identify_source_contract(file_path)
    validate_source_header(file_path, contract)

    rows_processed = 0

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:
            rows_processed += 1
            statistics["total_rows"] += 1

            if _is_malformed_row(row):
                statistics["invalid_rows"] += 1
                statistics["errors"]["malformed_row"] += 1
                continue

            errors = validate_row(row, contract.sensor)

            # A source version is provenance, not a floating-point
            # measurement. Preserve it exactly; only check that it exists.
            raw_version = row.get("version")

            if raw_version is None or not raw_version.strip():
                errors.append("version:missing")

            # Check every observation against the identity declared by
            # its folder and filename.
            try:
                validate_source_identity(
                    contract,
                    row.get("satellite"),
                    row.get("instrument"),
                )
            except ValueError as exc:
                errors.append("source_identity:invalid")
                statistics["source_identity_errors"][str(exc)] += 1

            # Quality flags are counted independently of validity.
            quality_flags = get_row_quality_flags(row)

            if quality_flags:
                statistics["quality_flagged_rows"] += 1

                for flag in quality_flags:
                    statistics["quality_flags"][flag] += 1

            if errors:
                statistics["invalid_rows"] += 1

                for error in errors:
                    statistics["errors"][error] += 1
            else:
                statistics["valid_rows"] += 1

    statistics["files_processed"] += 1

    print(
        f"Processed: {file_path.name} "
        f"| Rows in file: {rows_processed:,}"
    )


def main() -> None:
    """Validate all raw FIRMS CSV files without modifying them."""

    data_dir = get_data_directory()
    csv_files = sorted(data_dir.rglob("*.csv"))

    if not csv_files:
        print("No CSV files found.")
        return

    statistics = {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "files_processed": 0,
        "quality_flagged_rows": 0,
        "errors": Counter(),
        "quality_flags": Counter(),
        "source_identity_errors": Counter(),
    }

    print("SUTELLITE - RAW DATA VALIDATION")
    print("=" * 60)
    print(f"CSV files discovered: {len(csv_files)}")
    print()

    for file_path in csv_files:
        process_file(file_path, statistics)

    print()
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Files processed: {statistics['files_processed']:,}")
    print(f"Total observations: {statistics['total_rows']:,}")
    print(f"Valid observations: {statistics['valid_rows']:,}")
    print(f"Invalid observations: {statistics['invalid_rows']:,}")
    print(
        f"Quality-flagged observations: "
        f"{statistics['quality_flagged_rows']:,}"
    )

    if statistics["total_rows"] > 0:
        valid_percentage = (
            statistics["valid_rows"] / statistics["total_rows"]
        ) * 100

        print(f"Valid percentage: {valid_percentage:.4f}%")

    print()
    print("VALIDATION ERRORS")
    print("-" * 60)

    if statistics["errors"]:
        for error, count in statistics["errors"].most_common():
            print(f"{error}: {count:,}")
    else:
        print("No validation errors found.")

    print()
    print("QUALITY FLAGS")
    print("-" * 60)

    if statistics["quality_flags"]:
        for flag, count in statistics["quality_flags"].most_common():
            print(f"{flag}: {count:,}")
    else:
        print("No quality flags found.")

    if statistics["source_identity_errors"]:
        print()
        print("SOURCE IDENTITY DETAILS")
        print("-" * 60)

        for error, count in (
            statistics["source_identity_errors"].most_common()
        ):
            print(f"{error}: {count:,}")


if __name__ == "__main__":
    main()
