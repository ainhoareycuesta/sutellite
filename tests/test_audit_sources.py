"""Tests for the metadata-only NASA FIRMS source audit."""

import json
import tempfile
import unittest
from pathlib import Path

from src.audit_sources import audit_sources, write_audit_report
from src.source_contracts import (
    ARCHIVE_HEADER,
    FOLDER_CONTRACTS,
    NRT_HEADER,
    REGION_SLUGS,
)


def create_complete_dataset(root: Path) -> None:
    """Create a temporary dataset with all expected folders and files."""

    for region in REGION_SLUGS:
        for suffix, config in FOLDER_CONTRACTS.items():
            folder = root / f"{region}{suffix}"
            folder.mkdir(parents=True, exist_ok=True)

            product_token = config["product_token"]

            sources = (
                ("fire_archive", ARCHIVE_HEADER),
                ("fire_nrt", NRT_HEADER),
            )

            for filename_prefix, header in sources:
                filename = (
                    f"{filename_prefix}_{product_token}_838781.csv"
                )

                file_path = folder / filename

                file_path.write_text(
                    ",".join(header) + "\n",
                    encoding="utf-8",
                )


class TestSourceAudit(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        self.data_root = Path(self.temp_directory.name)

        create_complete_dataset(self.data_root)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_accepts_complete_dataset(self):
        report = audit_sources(self.data_root)

        expected_file_count = (
            len(REGION_SLUGS)
            * len(FOLDER_CONTRACTS)
            * 2
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(
            report["summary"]["expected_csv_files"],
            expected_file_count,
        )
        self.assertEqual(
            report["summary"]["discovered_csv_files"],
            expected_file_count,
        )
        self.assertEqual(
            report["summary"]["valid_files"],
            expected_file_count,
        )
        self.assertEqual(report["summary"]["invalid_files"], 0)

    def test_rejects_header_mismatch(self):
        file_path = (
            self.data_root
            / "angola_modis"
            / "fire_archive_M-C61_838781.csv"
        )

        file_path.write_text(
            "latitude,longitude\n",
            encoding="utf-8",
        )

        report = audit_sources(self.data_root)

        record = next(
            item
            for item in report["files"]
            if item["path"]
            == "angola_modis/fire_archive_M-C61_838781.csv"
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(record["status"], "INVALID")
        self.assertTrue(record["errors"])

    def test_reports_missing_nrt_file(self):
        file_path = (
            self.data_root
            / "angola_modis"
            / "fire_nrt_M-C61_838781.csv"
        )

        file_path.unlink()

        report = audit_sources(self.data_root)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            {
                "folder": "angola_modis",
                "stream": "NRT",
            },
            report["missing_streams"],
        )

    def test_reports_unrecognised_csv_filename(self):
        file_path = self.data_root / "angola_modis" / "unexpected.csv"

        file_path.write_text(
            ",".join(ARCHIVE_HEADER) + "\n",
            encoding="utf-8",
        )

        report = audit_sources(self.data_root)

        record = next(
            item
            for item in report["files"]
            if item["filename"] == "unexpected.csv"
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(record["status"], "INVALID")
        self.assertTrue(record["errors"])

    def test_reports_duplicate_stream(self):
        duplicate_path = (
            self.data_root
            / "angola_modis"
            / "fire_archive_M-C61_999999.csv"
        )

        duplicate_path.write_text(
            ",".join(ARCHIVE_HEADER) + "\n",
            encoding="utf-8",
        )

        report = audit_sources(self.data_root)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            {
                "folder": "angola_modis",
                "stream": "ARCHIVE",
                "count": 2,
            },
            report["duplicate_streams"],
        )

    def test_reports_missing_sensor_folder(self):
        folder_path = self.data_root / "angola_viirs_20"

        for file_path in folder_path.iterdir():
            file_path.unlink()

        folder_path.rmdir()

        report = audit_sources(self.data_root)

        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            "angola_viirs_20",
            report["missing_folders"],
        )

    def test_writes_json_report(self):
        report = audit_sources(self.data_root)
        output_path = self.data_root / "reports" / "audit.json"

        result_path = write_audit_report(report, output_path)

        self.assertTrue(result_path.exists())

        saved_report = json.loads(
            result_path.read_text(encoding="utf-8")
        )

        self.assertEqual(saved_report["status"], "PASS")
        self.assertEqual(
            saved_report["summary"]["discovered_csv_files"],
            report["summary"]["discovered_csv_files"],
        )


if __name__ == "__main__":
    unittest.main()