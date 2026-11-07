"""Audit the structure and source metadata of raw NASA FIRMS CSV files.

This audit checks:
- Expected region/sensor folders.
- CSV filenames and source contracts.
- Exact ARCHIVE and NRT headers.
- Missing or duplicated source files.

It does not read observation rows or modify raw source files.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.source_contracts import (
    FOLDER_CONTRACTS,
    REGION_SLUGS,
    identify_source_contract,
    validate_source_header,
)

from src.validate_data import get_data_directory


EXPECTED_STREAMS = ("ARCHIVE", "NRT")


def get_expected_folders() -> set[str]:
    """Return all expected region/sensor folder names."""

    return {
        f"{region}{suffix}".lower()
        for region in REGION_SLUGS
        for suffix in FOLDER_CONTRACTS
    }


def discover_csv_files(data_directory: Path) -> list[Path]:
    """Find CSV files recursively without reading their contents."""

    return sorted(
        path
        for path in data_directory.rglob("*")
        if path.is_file() and path.suffix.casefold() == ".csv"
    )


def audit_sources(data_directory: Path) -> dict:
    """Audit all CSV source files using filenames and headers only."""

    data_directory = Path(data_directory)

    if not data_directory.exists():
        raise FileNotFoundError(
            f"Data directory does not exist: {data_directory}"
        )

    if not data_directory.is_dir():
        raise NotADirectoryError(
            f"Data path is not a directory: {data_directory}"
        )

    expected_folders = get_expected_folders()

    actual_folders = {
        path.name.casefold()
        for path in data_directory.iterdir()
        if path.is_dir()
    }

    missing_folders = sorted(expected_folders - actual_folders)
    unexpected_directories = sorted(actual_folders - expected_folders)

    csv_files = discover_csv_files(data_directory)

    file_records = []
    stream_counts: Counter[tuple[str, str]] = Counter()

    for file_path in csv_files:
        errors = []
        contract = None
        header_columns = None

        try:
            contract = identify_source_contract(file_path)

            # Count identified sources even if their headers are invalid.
            stream_counts[
                (
                    contract.sensor_folder,
                    contract.processing_stream,
                )
            ] += 1

            header = validate_source_header(file_path, contract)
            header_columns = len(header)

        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(str(exc))

        record = {
            "path": file_path.relative_to(data_directory).as_posix(),
            "filename": file_path.name,
            "folder": file_path.parent.name,
            "status": "VALID" if not errors else "INVALID",
            "header_columns": header_columns,
            "errors": errors,
        }

        if contract is not None:
            record.update(
                {
                    "region_id": contract.region_id,
                    "sensor": contract.sensor,
                    "platform_group": contract.platform_group,
                    "collection": contract.collection,
                    "product_token": contract.product_token,
                    "processing_stream": contract.processing_stream,
                    "processing_provider": contract.processing_provider,
                    "source_id": contract.source_id,
                }
            )

        file_records.append(record)

    missing_streams = []
    duplicate_streams = []

    for folder in sorted(expected_folders):
        for stream in EXPECTED_STREAMS:
            count = stream_counts[(folder, stream)]

            if count == 0:
                missing_streams.append(
                    {
                        "folder": folder,
                        "stream": stream,
                    }
                )

            elif count > 1:
                duplicate_streams.append(
                    {
                        "folder": folder,
                        "stream": stream,
                        "count": count,
                    }
                )

    valid_files = sum(
        record["status"] == "VALID"
        for record in file_records
    )

    invalid_files = len(file_records) - valid_files

    audit_passed = (
        not missing_folders
        and not missing_streams
        and not duplicate_streams
        and invalid_files == 0
    )

    return {
        "generated_at_utc": (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        ),
        "data_directory": data_directory.name,
        "scope": (
            "Metadata only: folder names, filenames, source contracts "
            "and CSV headers. Observation rows were not read."
        ),
        "status": "PASS" if audit_passed else "FAIL",
        "summary": {
            "expected_folders": len(expected_folders),
            "found_expected_folders": len(
                expected_folders & actual_folders
            ),
            "missing_folders": len(missing_folders),
            "unexpected_directories": len(unexpected_directories),
            "expected_csv_files": len(expected_folders) * len(
                EXPECTED_STREAMS
            ),
            "discovered_csv_files": len(csv_files),
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "missing_streams": len(missing_streams),
            "duplicate_streams": len(duplicate_streams),
        },
        "missing_folders": missing_folders,
        "unexpected_directories": unexpected_directories,
        "missing_streams": missing_streams,
        "duplicate_streams": duplicate_streams,
        "files": file_records,
    }


def write_audit_report(
    report: dict,
    output_path: Path,
) -> Path:
    """Write the audit results as a JSON report."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    return output_path


def main() -> None:
    """Run the metadata audit and save its report."""

    data_directory = get_data_directory()
    report = audit_sources(data_directory)

    project_root = Path(__file__).resolve().parents[1]

    timestamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    )

    output_path = (
        project_root
        / "reports"
        / "source_audits"
        / f"source_audit_{timestamp}.json"
    )

    write_audit_report(report, output_path)

    summary = report["summary"]

    print("\nNASA FIRMS SOURCE AUDIT")
    print("=" * 40)
    print(f"Status:                 {report['status']}")
    print(f"Expected folders:       {summary['expected_folders']}")
    print(f"Found expected folders: {summary['found_expected_folders']}")
    print(f"Expected CSV files:     {summary['expected_csv_files']}")
    print(f"Discovered CSV files:   {summary['discovered_csv_files']}")
    print(f"Valid files:            {summary['valid_files']}")
    print(f"Invalid files:          {summary['invalid_files']}")
    print(f"Missing folders:        {summary['missing_folders']}")
    print(f"Missing streams:        {summary['missing_streams']}")
    print(f"Duplicate streams:      {summary['duplicate_streams']}")
    print(f"\nReport saved to: {output_path}")

    if report["status"] == "FAIL":
        print("\nThe audit found issues. Inspect the JSON report.")
        raise SystemExit(1)

    print("\nAll source metadata checks passed.")


if __name__ == "__main__":
    main()