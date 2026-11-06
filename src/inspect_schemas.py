
from pathlib import Path
import csv

# Original NASA FIRMS data directory
DATA_DIR = Path(
    r"C:\Users\rey.ainhoa\OneDrive - Universidad de Deusto\Documentos\datos_modis_viirs"
)

# Files to inspect
FILES = {
    "MODIS_ARCHIVE": DATA_DIR / "angola_modis" / "fire_archive_M-C61_838781.csv",
    "MODIS_NRT": DATA_DIR / "angola_modis" / "fire_nrt_M-C61_838781.csv",
    "VIIRS_ARCHIVE": DATA_DIR / "angola_viirs_snpp" / "fire_archive_SV-C2_838784.csv",
    "VIIRS_NRT": DATA_DIR / "angola_viirs_snpp" / "fire_nrt_SV-C2_838784.csv",
}


def read_csv_header(file_path: Path) -> list[str]:
    """Read the column names without loading the observations."""
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        return next(reader)



def main():
    print("SUTELLITE - CSV SCHEMA INSPECTION")
    print("=" * 50)

    schemas = {}

    for product, file_path in FILES.items():
        if not file_path.exists():
            print(f"\n[ERROR] File not found: {file_path}")
            continue

        columns = read_csv_header(file_path)
        schemas[product] = columns

        print(f"\n{product}: {len(columns)} columns")

    if not schemas:
        print("\nNo files were successfully inspected.")
        return

    # Use all column names found across the products
    all_columns = set()

    for columns in schemas.values():
        all_columns.update(columns)

    print("\n" + "=" * 50)
    print("FIELD PRESENCE COMPARISON")
    print("=" * 50)

    for column in sorted(all_columns):
        print(f"\n{column}")

        for product, columns in schemas.items():
            status = "PRESENT" if column in columns else "MISSING"
            print(f"  {product}: {status}")


if __name__ == "__main__":
    main()