import csv
import os
from pathlib import Path
from collections import Counter, defaultdict

from dotenv import load_dotenv

def identify_sensor(folder_name: str) -> str:
    """Identify the sensor from its parent folder name."""

    if folder_name.endswith("_modis"):
        return "MODIS"

    if folder_name.endswith("_viirs_snpp"):
        return "VIIRS_SNPP"

    if folder_name.endswith("_viirs_20"):
        return "VIIRS_NOAA20"

    if folder_name.endswith("_viirs_21"):
        return "VIIRS_NOAA21"

    return "UNKNOWN"

def identify_product(filename: str) -> str:
    """Identify the FIRMS product from its filename."""

    if filename.startswith("fire_archive"):
        return "ARCHIVE"

    if filename.startswith("fire_nrt"):
        return "NRT"

    return "UNKNOWN"

def create_statistics() -> dict:
    """Create an empty statistics structure for one sensor/product group."""

    return {
        "rows": 0,
        "missing": Counter(),
        "values": defaultdict(Counter),
        "date_min": None,
        "date_max": None,
        "available_fields": set(),
    }

FIELDS_TO_PROFILE = [
    "confidence",
    "type",
    "satellite",
    "instrument",
    "version",
    "daynight",
]

def process_file(file_path: Path, stats: dict) -> None:
    """Read a CSV progressively and update its statistics."""

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        stats["available_fields"] = set(reader.fieldnames or [])

        for row in reader:
            stats["rows"] += 1

            for field in FIELDS_TO_PROFILE:
                if field not in stats["available_fields"]:
                    continue
                value = row.get(field)

                if value is None or not value.strip():
                    stats["missing"][field] += 1
                else:
                    stats["values"][field][value.strip()] += 1

            date = row.get("acq_date")

            if date:
                if stats["date_min"] is None or date < stats["date_min"]:
                    stats["date_min"] = date

                if stats["date_max"] is None or date > stats["date_max"]:
                    stats["date_max"] = date

def main():
    load_dotenv()

    data_dir = os.getenv("SUTELLITE_DATA_DIR")

    if not data_dir:
        raise SystemExit("ERROR: SUTELLITE_DATA_DIR is not configured.")

    raw_dir = Path(data_dir)

    if not raw_dir.is_dir():
        raise SystemExit(f"ERROR: Data directory not found: {raw_dir}")

    csv_files = sorted(raw_dir.rglob("*.csv"))

    if not csv_files:
        raise SystemExit("ERROR: No CSV files found.")

    statistics = {}

    print("SUTELLITE - FULL DATA PROFILING")
    print("=" * 70)
    print(f"CSV files discovered: {len(csv_files)}")
    print("Starting full scan...\n")

    total_rows = 0

    for index, file_path in enumerate(csv_files, start=1):
        sensor = identify_sensor(file_path.parent.name)
        product = identify_product(file_path.name)

        if sensor == "UNKNOWN" or product == "UNKNOWN":
            print(f"Skipping unrecognised file: {file_path.name}")
            continue

        group = (sensor, product)

        if group not in statistics:
            statistics[group] = create_statistics()

        print(f"[{index}/{len(csv_files)}] Processing: {file_path.name}")

        process_file(file_path, statistics[group])

        rows = statistics[group]["rows"]
        print(f"    Group observations so far: {rows:,}")

    total_rows = sum(
        stats["rows"] for stats in statistics.values()
    )

    print("\n" + "=" * 70)
    print("SCAN COMPLETED")
    print(f"Total observations: {total_rows:,}")
    print(f"Groups inspected: {len(statistics)}")
    print_report(statistics)

def print_report(statistics: dict) -> None:
    """Print the collected statistics for every sensor/product group."""

    print("\n" + "=" * 70)
    print("DETAILED DATA PROFILE")
    print("=" * 70)

    for (sensor, product), stats in sorted(statistics.items()):
        print(f"\n{sensor} / {product}")
        print("-" * 70)

        print(f"Total observations: {stats['rows']:,}")
        print(f"Date range: {stats['date_min']} to {stats['date_max']}")

        for field in FIELDS_TO_PROFILE:
            if field not in stats["available_fields"]:
                print(f"\n{field}: NOT AVAILABLE IN THIS PRODUCT")
                continue

            print(f"\n{field.upper()}")

            values = stats["values"][field]

            for value, count in sorted(values.items()):
                print(f"  {value}: {count:,}")

            missing = stats["missing"][field]

            print(f"  Missing: {missing:,}")

if __name__ == "__main__":
    main()