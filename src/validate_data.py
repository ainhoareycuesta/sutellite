
import csv
import math
import os
from pathlib import Path
from collections import Counter
from datetime import datetime

from dotenv import load_dotenv


# Fields that require numeric validation
NUMERIC_FIELDS = [
    "latitude",
    "longitude",
    "brightness",
    "scan",
    "track",
    "bright_t31",
    "frp",
]

# Allowed categorical values
ALLOWED_DAYNIGHT = {"D", "N"}
ALLOWED_VIIRS_CONFIDENCE = {"l", "n", "h"}
ALLOWED_DETECTION_TYPES = {"0", "1", "2", "3"}


def get_data_directory() -> Path:
    """Load and return the raw data directory."""

    load_dotenv()

    data_dir = os.getenv("SUTELLITE_DATA_DIR")

    if not data_dir:
        raise EnvironmentError(
            "SUTELLITE_DATA_DIR is not configured in the .env file."
        )

    path = Path(data_dir)

    if not path.exists():
        raise FileNotFoundError(f"Data directory not found: {path}")

    return path


def validate_numeric_field(field: str, value: str | None) -> str | None:
    """Validate that a field contains a valid numeric value."""

    if value is None or value.strip() == "":
        return "missing"

    try:
        number = float(value)
    except ValueError:
        return "not_numeric"

    if not math.isfinite(number):
        return "not_finite"

    if field == "latitude" and not -90 <= number <= 90:
        return "out_of_range"

    if field == "longitude" and not -180 <= number <= 180:
        return "out_of_range"

    if field in {"scan", "track"} and number <= 0:
        return "out_of_range"

    if field == "frp" and number < 0:
        return "out_of_range"

    return None


def validate_date(value: str | None) -> str | None:
    """Validate acquisition date format and calendar validity."""

    if not value:
        return "missing"

    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return "invalid_date"

    return None


def validate_time(value: str | None) -> str | None:
    """Validate acquisition time in HHMM format."""

    if not value:
        return "missing"

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
    sensor: str
) -> str | None:
    """Validate categorical fields according to the sensor."""

    if value is None or value.strip() == "":
        return "missing"

    value = value.strip()

    if field == "daynight" and value not in ALLOWED_DAYNIGHT:
        return "invalid_category"

    if field == "confidence":
        if sensor == "MODIS":
            try:
                confidence = float(value)
            except ValueError:
                return "not_numeric"

            if not math.isfinite(confidence) or not 0 <= confidence <= 100:
                return "out_of_range"

        elif value.lower() not in ALLOWED_VIIRS_CONFIDENCE:
            return "invalid_category"

    return None


def validate_row(row: dict, sensor: str) -> list[str]:
    """Validate one CSV observation and return its errors."""

    errors = []

    # Validate numeric fields
    for field in NUMERIC_FIELDS:
        result = validate_numeric_field(field, row.get(field))

        if result:
            errors.append(f"{field}:{result}")

    # Validate acquisition date
    result = validate_date(row.get("acq_date"))

    if result:
        errors.append(f"acq_date:{result}")

    # Validate acquisition time
    result = validate_time(row.get("acq_time"))

    if result:
        errors.append(f"acq_time:{result}")

    # Validate categorical fields
    for field in ["confidence", "daynight"]:
        result = validate_categorical_field(
            field,
            row.get(field),
            sensor
        )

        if result:
            errors.append(f"{field}:{result}")

    # Validate detection type when available
    detection_type = row.get("type")

    if detection_type is not None:
        if detection_type.strip() == "":
            errors.append("type:missing")
        elif detection_type.strip() not in ALLOWED_DETECTION_TYPES:
            errors.append("type:invalid_category")

    return errors


def identify_sensor(file_path: Path) -> str:
    """Identify the sensor configuration from the source folder."""

    folder_name = file_path.parent.name.lower()

    if "_modis" in folder_name:
        return "MODIS"

    if "_viirs" in folder_name:
        return "VIIRS"

    raise ValueError(f"Unknown sensor configuration: {folder_name}")


def process_file(file_path: Path, statistics: dict) -> None:
    """Validate a CSV file row by row."""

    sensor = identify_sensor(file_path)

    with file_path.open(
        "r",
        encoding="utf-8",
        newline=""
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        expected_fields = set(reader.fieldnames or [])

        required_fields = set(NUMERIC_FIELDS) | {
            "acq_date",
            "acq_time",
            "confidence",
            "daynight",
        }

        if not required_fields.issubset(expected_fields):
            missing_fields = required_fields - expected_fields
            raise ValueError(
                f"Missing required columns in {file_path.name}: "
                f"{sorted(missing_fields)}"
            )

        is_archive = file_path.name.startswith("fire_archive")

        if is_archive and "type" not in expected_fields:
            raise ValueError(
                f"ARCHIVE file is missing the required 'type' column: "
                f"{file_path.name}"
            )

        if not is_archive and "type" in expected_fields:
            raise ValueError(
                f"NRT file unexpectedly contains a 'type' column: "
                f"{file_path.name}"
            )

        for row in reader:
            statistics["total_rows"] += 1

            # Detect malformed CSV rows with extra or missing columns
            if None in row or any(value is None for value in row.values()):
                statistics["invalid_rows"] += 1
                statistics["errors"]["malformed_row"] += 1
                continue

            errors = validate_row(row, sensor)

            if errors:
                statistics["invalid_rows"] += 1

                for error in errors:
                    statistics["errors"][error] += 1

            else:
                statistics["valid_rows"] += 1

    statistics["files_processed"] += 1

    print(
        f"Processed: {file_path.name} "
        f"| Total rows: {statistics['total_rows']:,}"
    )


def main() -> None:
    """Validate all raw CSV files."""

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
        "errors": Counter(),
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
    print(f"Files processed: {statistics['files_processed']}")
    print(f"Total observations: {statistics['total_rows']:,}")
    print(f"Valid observations: {statistics['valid_rows']:,}")
    print(f"Invalid observations: {statistics['invalid_rows']:,}")

    if statistics["total_rows"] > 0:
        valid_percentage = (
            statistics["valid_rows"] / statistics["total_rows"]
        ) * 100

        print(f"Valid percentage: {valid_percentage:.4f}%")

    print()
    print("ERROR BREAKDOWN")
    print("-" * 60)

    if statistics["errors"]:
        for error, count in statistics["errors"].most_common():
            print(f"{error}: {count:,}")
    else:
        print("No validation errors found.")


if __name__ == "__main__":
    main()
