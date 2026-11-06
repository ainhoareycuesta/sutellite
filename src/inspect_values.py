
import csv
import os
from pathlib import Path

from dotenv import load_dotenv


def identify_sensor(folder_name: str) -> str:
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
    if filename.startswith("fire_archive"):
        return "ARCHIVE"

    if filename.startswith("fire_nrt"):
        return "NRT"

    return "UNKNOWN"


def main():
    load_dotenv()

    data_dir = os.getenv("SUTELLITE_DATA_DIR")

    if not data_dir:
        raise SystemExit("ERROR: SUTELLITE_DATA_DIR is not configured.")

    raw_dir = Path(data_dir)

    if not raw_dir.is_dir():
        raise SystemExit(f"ERROR: Data directory not found: {raw_dir}")

    inspected = set()

    print("SUTELLITE - CSV VALUE INSPECTION")
    print("=" * 70)

    for file_path in sorted(raw_dir.rglob("*.csv")):
        sensor = identify_sensor(file_path.parent.name)
        product = identify_product(file_path.name)

        group = (sensor, product)

        if group in inspected:
            continue

        inspected.add(group)

        print(f"\n{sensor} / {product}")
        print("-" * 70)
        print(f"File: {file_path.name}")

        with file_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)

            for row_number, row in enumerate(reader, start=1):
                if row_number > 5:
                    break

                fields = [
                    "satellite",
                    "instrument",
                    "confidence",
                    "version",
                    "type",
                    "daynight",
                    "acq_date",
                    "acq_time",
                ]

                values = [
                    f"{field}={row.get(field, 'N/A')}"
                    for field in fields
                    if field in row
                ]

                print(f"  Row {row_number}: " + " | ".join(values))


if __name__ == "__main__":
    main()
