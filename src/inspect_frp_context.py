
import csv
import os
from pathlib import Path
from dotenv import load_dotenv


def main():
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    data_dir = Path(os.getenv("SUTELLITE_DATA_DIR", ""))

    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    findings_file = project_root / "docs" / "data" / "NEGATIVE_FRP_RECORDS.csv"

    with findings_file.open("r", encoding="utf-8", newline="") as file:
        findings = list(csv.DictReader(file))

    records_by_file = {}

    for finding in findings:
        relative_path = finding["file"]
        row_number = int(finding["row"])
        records_by_file.setdefault(relative_path, set()).add(row_number)

    fields = [
        "file",
        "row",
        "frp",
        "latitude",
        "longitude",
        "acq_date",
        "acq_time",
        "brightness",
        "bright_t31",
        "confidence",
        "version",
        "daynight",
        "scan",
        "track",
        "type",
        "satellite",
        "instrument",
    ]

    results = []

    for relative_path, target_rows in records_by_file.items():
        file_path = data_dir / relative_path
        print(f"Inspecting: {relative_path}")

        with file_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            for row_number, row in enumerate(reader, start=2):
                if row_number not in target_rows:
                    continue

                result = {
                    "file": relative_path,
                    "row": row_number,
                }

                for field in fields:
                    if field not in ("file", "row"):
                        result[field] = row.get(field, "")

                results.append(result)

                if len(results) == len(findings):
                    break

    output_file = project_root / "docs" / "data" / "NEGATIVE_FRP_CONTEXT.csv"

    with output_file.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)

    print("\nSUMMARY")
    print("=" * 50)
    print(f"Expected records: {len(findings)}")
    print(f"Records retrieved: {len(results)}")
    print(f"Source files inspected: {len(records_by_file)}")
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    main()
