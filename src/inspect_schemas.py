
from pathlib import Path
import csv
import os
from collections import defaultdict
from dotenv import load_dotenv


def read_csv_header(file_path: Path) -> list[str]:
    """Read CSV column names without loading observations."""
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        return next(reader)


def identify_product(file_path: Path) -> str:
    """Identify the product type from its filename."""
    if file_path.name.startswith("fire_archive"):
        return "ARCHIVE"

    if file_path.name.startswith("fire_nrt"):
        return "NRT"

    return "UNKNOWN"


def identify_sensor(folder_name: str) -> str:
    """Identify the sensor from the folder name."""
    if folder_name.endswith("_modis"):
        return "MODIS"

    if folder_name.endswith("_viirs_snpp"):
        return "VIIRS_SNPP"

    if folder_name.endswith("_viirs_20"):
        return "VIIRS_NOAA20"

    if folder_name.endswith("_viirs_21"):
        return "VIIRS_NOAA21"

    return "UNKNOWN"


def main():
    load_dotenv()

    data_dir = os.getenv("SUTELLITE_DATA_DIR")

    if not data_dir:
        raise SystemExit("ERROR: SUTELLITE_DATA_DIR is not configured.")

    raw_dir = Path(data_dir)

    if not raw_dir.is_dir():
        raise SystemExit(f"ERROR: Data directory not found: {raw_dir}")

    schemas = {}
    groups = defaultdict(list)

    csv_files = sorted(raw_dir.rglob("*.csv"))

    print("SUTELLITE - CSV SCHEMA INSPECTION")
    print("=" * 60)
    print(f"CSV files discovered: {len(csv_files)}")

    for file_path in csv_files:
        folder_name = file_path.parent.name
        sensor = identify_sensor(folder_name)
        product = identify_product(file_path)

        columns = read_csv_header(file_path)

        schemas[file_path] = columns
        groups[(sensor, product)].append(file_path)

    print("\nFILES INSPECTED")
    print("-" * 60)

    for (sensor, product), files in sorted(groups.items()):
        print(f"{sensor} / {product}: {len(files)} files")

        print("\nEXACT SCHEMA COMPARISON")
        print("-" * 60)

        for (sensor, product), files in sorted(groups.items()):
            unique_schemas = {
                tuple(schemas[file_path])
                for file_path in files
            }

            print(
                f"{sensor} / {product}: "
                f"{len(unique_schemas)} unique schema(s)"
            )

            for schema in unique_schemas:
                print(f"  Columns: {len(schema)}")
                print(f"  Order: {', '.join(schema)}")

    if not schemas:
        print("\nNo CSV files found.")
        return

    all_columns = set()

    for columns in schemas.values():
        all_columns.update(columns)

    print("\nFIELD PRESENCE COMPARISON")
    print("-" * 60)

    for column in sorted(all_columns):
        present = sum(
            column in columns
            for columns in schemas.values()
        )

        missing = len(schemas) - present

        print(
            f"{column:<20} "
            f"Present: {present:>2}/{len(schemas)} "
            f"Missing: {missing:>2}"
        )


if __name__ == "__main__":
    main()