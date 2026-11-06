
import csv
import os
from pathlib import Path
from dotenv import load_dotenv


def main():
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    data_dir = os.getenv("SUTELLITE_DATA_DIR")

    if not data_dir:
        raise ValueError("SUTELLITE_DATA_DIR is not configured in .env")

    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    results = []
    files_scanned = 0

    print("SUTELLITE - NEGATIVE FRP INVESTIGATION")
    print("=" * 50)

    for file_path in sorted(data_path.rglob("*.csv")):
        files_scanned += 1

        with file_path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames or "frp" not in reader.fieldnames:
                continue

            for row_number, row in enumerate(reader, start=2):
                try:
                    frp = float(row["frp"])
                except (ValueError, TypeError):
                    continue

                if frp < 0:
                    result = {
                        "file": str(file_path.relative_to(data_path)),
                        "row": row_number,
                        "frp": frp,
                        "latitude": row.get("latitude", ""),
                        "longitude": row.get("longitude", ""),
                        "acq_date": row.get("acq_date", ""),
                        "satellite": row.get("satellite", ""),
                        "instrument": row.get("instrument", ""),
                    }

                    results.append(result)

                    print(
                        f"{result['file']} | "
                        f"Row {row_number} | "
                        f"FRP: {frp}"
                    )

    output_dir = project_root / "docs" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "NEGATIVE_FRP_RECORDS.csv"

    fieldnames = [
        "file", "row", "frp", "latitude",
        "longitude", "acq_date", "satellite", "instrument"
    ]

    with output_file.open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print("\nSUMMARY")
    print("=" * 50)
    print(f"Files scanned: {files_scanned}")
    print(f"Negative FRP observations: {len(results)}")
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()
