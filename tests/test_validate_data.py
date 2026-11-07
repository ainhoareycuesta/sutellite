
import csv
import unittest
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from src.source_contracts import ARCHIVE_HEADER, NRT_HEADER
from src.validate_data import (
    get_row_quality_flags,
    process_file,
    validate_categorical_field,
    validate_date,
    validate_numeric_field,
    validate_row,
    validate_time,
)


def make_archive_row(**overrides):
    """Create a representative MODIS ARCHIVE observation."""

    row = {
        "latitude": "12.5",
        "longitude": "18.3",
        "brightness": "320.4",
        "scan": "1.0",
        "track": "1.0",
        "acq_date": "2024-01-15",
        "acq_time": "1234",
        "satellite": "Terra",
        "instrument": "MODIS",
        "confidence": "75",
        "version": "6.03",
        "bright_t31": "290.2",
        "frp": "12.5",
        "daynight": "D",
        "type": "0",
    }

    row.update(overrides)
    return row


def make_viirs_nrt_row(**overrides):
    """Create a representative VIIRS NRT observation."""

    row = {
        "latitude": "-12.5",
        "longitude": "18.3",
        "brightness": "367.0",
        "scan": "0.4",
        "track": "0.4",
        "acq_date": "2024-01-15",
        "acq_time": "0034",
        "satellite": "N20",
        "instrument": "VIIRS",
        "confidence": "n",
        "version": "2.0NRT",
        "bright_t31": "310.2",
        "frp": "5.2",
        "daynight": "N",
    }

    row.update(overrides)
    return row


def make_statistics():
    return {
        "total_rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "files_processed": 0,
        "quality_flagged_rows": 0,
        "errors": Counter(),
        "quality_flags": Counter(),
        "source_identity_errors": Counter(),
    }


def write_source_file(
    folder: Path,
    filename: str,
    header: tuple[str, ...],
    row: dict,
) -> Path:
    """Write a small temporary CSV fixture for tests."""

    folder.mkdir(parents=True, exist_ok=True)
    file_path = folder / filename

    with file_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=header,
        )
        writer.writeheader()
        writer.writerow(row)

    return file_path


class TestNumericValidation(unittest.TestCase):

    def test_valid_coordinates(self):
        self.assertIsNone(
            validate_numeric_field("latitude", "45.5")
        )
        self.assertIsNone(
            validate_numeric_field("longitude", "-120.2")
        )

    def test_invalid_latitude(self):
        self.assertEqual(
            validate_numeric_field("latitude", "91"),
            "out_of_range",
        )

    def test_invalid_longitude(self):
        self.assertEqual(
            validate_numeric_field("longitude", "-181"),
            "out_of_range",
        )

    def test_missing_numeric_value(self):
        self.assertEqual(
            validate_numeric_field("brightness", None),
            "missing",
        )

    def test_non_numeric_value(self):
        self.assertEqual(
            validate_numeric_field("brightness", "unknown"),
            "not_numeric",
        )

    def test_non_finite_value(self):
        self.assertEqual(
            validate_numeric_field("frp", "NaN"),
            "not_finite",
        )
        self.assertEqual(
            validate_numeric_field("frp", "inf"),
            "not_finite",
        )

    def test_scan_and_track_must_be_positive(self):
        self.assertEqual(
            validate_numeric_field("scan", "0"),
            "out_of_range",
        )
        self.assertEqual(
            validate_numeric_field("track", "-1"),
            "out_of_range",
        )

    def test_negative_frp_is_not_rejected(self):
        self.assertIsNone(
            validate_numeric_field("frp", "-0.66")
        )


class TestDateTimeValidation(unittest.TestCase):

    def test_valid_date(self):
        self.assertIsNone(validate_date("2024-01-15"))

    def test_invalid_date_format(self):
        self.assertEqual(
            validate_date("15-01-2024"),
            "invalid_date",
        )

    def test_invalid_calendar_date(self):
        self.assertEqual(
            validate_date("2024-02-30"),
            "invalid_date",
        )

    def test_missing_date(self):
        self.assertEqual(validate_date(None), "missing")

    def test_valid_time(self):
        self.assertIsNone(validate_time("0034"))
        self.assertIsNone(validate_time("2359"))
        self.assertIsNone(validate_time("0000"))

    def test_invalid_time_format(self):
        self.assertEqual(
            validate_time("123"),
            "invalid_time",
        )

    def test_invalid_time_values(self):
        self.assertEqual(
            validate_time("2460"),
            "invalid_time",
        )
        self.assertEqual(
            validate_time("1260"),
            "invalid_time",
        )

    def test_missing_time(self):
        self.assertEqual(validate_time(None), "missing")


class TestCategoricalValidation(unittest.TestCase):

    def test_modis_confidence(self):
        self.assertIsNone(
            validate_categorical_field(
                "confidence",
                "75",
                "MODIS",
            )
        )

    def test_modis_confidence_accepts_numeric_percentage(self):
        self.assertIsNone(
            validate_categorical_field(
                "confidence",
                "75.5",
                "MODIS",
            )
        )

    def test_invalid_modis_confidence(self):
        self.assertEqual(
            validate_categorical_field(
                "confidence",
                "high",
                "MODIS",
            ),
            "not_numeric",
        )

    def test_modis_confidence_out_of_range(self):
        self.assertEqual(
            validate_categorical_field(
                "confidence",
                "101",
                "MODIS",
            ),
            "out_of_range",
        )

    def test_viirs_confidence(self):
        for value in ("l", "n", "h", "L", "N", "H"):
            with self.subTest(value=value):
                self.assertIsNone(
                    validate_categorical_field(
                        "confidence",
                        value,
                        "VIIRS",
                    )
                )

    def test_invalid_viirs_confidence(self):
        self.assertEqual(
            validate_categorical_field(
                "confidence",
                "75",
                "VIIRS",
            ),
            "invalid_category",
        )

    def test_valid_daynight(self):
        self.assertIsNone(
            validate_categorical_field("daynight", "D", "MODIS")
        )
        self.assertIsNone(
            validate_categorical_field("daynight", "N", "VIIRS")
        )

    def test_invalid_daynight(self):
        self.assertEqual(
            validate_categorical_field(
                "daynight",
                "X",
                "MODIS",
            ),
            "invalid_category",
        )

    def test_valid_detection_type(self):
        for value in ("0", "1", "2", "3"):
            with self.subTest(value=value):
                self.assertIsNone(
                    validate_categorical_field(
                        "type",
                        value,
                        "MODIS",
                    )
                )

    def test_invalid_detection_type(self):
        self.assertEqual(
            validate_categorical_field(
                "type",
                "4",
                "MODIS",
            ),
            "invalid_category",
        )

    def test_missing_categorical_value(self):
        self.assertEqual(
            validate_categorical_field(
                "daynight",
                None,
                "MODIS",
            ),
            "missing",
        )


class TestRowValidation(unittest.TestCase):

    def test_valid_modis_archive_row(self):
        errors = validate_row(make_archive_row(), "MODIS")
        self.assertEqual(errors, [])

    def test_valid_viirs_nrt_row(self):
        errors = validate_row(make_viirs_nrt_row(), "VIIRS")
        self.assertEqual(errors, [])

    def test_invalid_coordinate_is_reported(self):
        row = make_archive_row(latitude="95")
        errors = validate_row(row, "MODIS")

        self.assertIn("latitude:out_of_range", errors)

    def test_invalid_confidence_is_reported(self):
        row = make_viirs_nrt_row(confidence="high")
        errors = validate_row(row, "VIIRS")

        self.assertIn("confidence:invalid_category", errors)

    def test_archive_type_is_validated(self):
        row = make_archive_row(type="9")
        errors = validate_row(row, "MODIS")

        self.assertIn("type:invalid_category", errors)

    def test_nrt_row_does_not_require_type(self):
        row = make_viirs_nrt_row()
        self.assertNotIn("type", row)

        errors = validate_row(row, "VIIRS")
        self.assertEqual(errors, [])

    def test_negative_frp_does_not_invalidate_row(self):
        row = make_archive_row(frp="-0.66")
        errors = validate_row(row, "MODIS")

        self.assertEqual(errors, [])


class TestQualityFlags(unittest.TestCase):

    def test_negative_frp_is_flagged(self):
        row = make_archive_row(frp="-0.66")

        self.assertEqual(
            get_row_quality_flags(row),
            ["negative_frp"],
        )

    def test_positive_frp_has_no_quality_flags(self):
        row = make_archive_row(frp="12.5")

        self.assertEqual(
            get_row_quality_flags(row),
            [],
        )

    def test_missing_frp_has_no_quality_flags(self):
        row = make_archive_row(frp="")

        self.assertEqual(
            get_row_quality_flags(row),
            [],
        )

    def test_invalid_frp_does_not_create_negative_flag(self):
        row = make_archive_row(frp="unknown")

        self.assertEqual(
            get_row_quality_flags(row),
            [],
        )


class TestFileProcessing(unittest.TestCase):

    def test_processes_valid_archive_file(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = write_source_file(
                root / "angola_modis",
                "fire_archive_M-C61_838781.csv",
                ARCHIVE_HEADER,
                make_archive_row(),
            )

            statistics = make_statistics()
            process_file(file_path, statistics)

            self.assertEqual(statistics["files_processed"], 1)
            self.assertEqual(statistics["total_rows"], 1)
            self.assertEqual(statistics["valid_rows"], 1)
            self.assertEqual(statistics["invalid_rows"], 0)

    def test_processes_valid_nrt_file_without_type(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = write_source_file(
                root / "angola_viirs_20",
                "fire_nrt_J1V-C2_838782.csv",
                NRT_HEADER,
                make_viirs_nrt_row(),
            )

            statistics = make_statistics()
            process_file(file_path, statistics)

            self.assertEqual(statistics["files_processed"], 1)
            self.assertEqual(statistics["total_rows"], 1)
            self.assertEqual(statistics["valid_rows"], 1)
            self.assertEqual(statistics["invalid_rows"], 0)

    def test_negative_frp_is_valid_but_quality_flagged(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = write_source_file(
                root / "angola_modis",
                "fire_archive_M-C61_838781.csv",
                ARCHIVE_HEADER,
                make_archive_row(frp="-0.66"),
            )

            statistics = make_statistics()
            process_file(file_path, statistics)

            self.assertEqual(statistics["valid_rows"], 1)
            self.assertEqual(statistics["invalid_rows"], 0)
            self.assertEqual(statistics["quality_flagged_rows"], 1)
            self.assertEqual(
                statistics["quality_flags"]["negative_frp"],
                1,
            )

    def test_source_identity_mismatch_invalidates_row(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = write_source_file(
                root / "angola_viirs_20",
                "fire_archive_J1V-C2_838782.csv",
                ARCHIVE_HEADER,
                make_archive_row(
                    satellite="N21",
                    instrument="VIIRS",
                    confidence="n",
                ),
            )

            statistics = make_statistics()
            process_file(file_path, statistics)

            self.assertEqual(statistics["valid_rows"], 0)
            self.assertEqual(statistics["invalid_rows"], 1)
            self.assertEqual(
                statistics["errors"]["source_identity:invalid"],
                1,
            )

    def test_missing_version_invalidates_row(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_path = write_source_file(
                root / "angola_modis",
                "fire_archive_M-C61_838781.csv",
                ARCHIVE_HEADER,
                make_archive_row(version=""),
            )

            statistics = make_statistics()
            process_file(file_path, statistics)

            self.assertEqual(statistics["valid_rows"], 0)
            self.assertEqual(statistics["invalid_rows"], 1)
            self.assertEqual(
                statistics["errors"]["version:missing"],
                1,
            )

    def test_header_mismatch_rejected_before_processing(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            wrong_header = list(ARCHIVE_HEADER)
            wrong_header[0], wrong_header[1] = (
                wrong_header[1],
                wrong_header[0],
            )

            folder = root / "angola_modis"
            folder.mkdir(parents=True)
            file_path = folder / "fire_archive_M-C61_838781.csv"

            with file_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(wrong_header)

            statistics = make_statistics()

            with self.assertRaises(ValueError):
                process_file(file_path, statistics)

            self.assertEqual(statistics["files_processed"], 0)
            self.assertEqual(statistics["total_rows"], 0)

    def test_malformed_row_is_counted_as_invalid(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            folder = root / "angola_modis"
            folder.mkdir(parents=True)
            file_path = folder / "fire_archive_M-C61_838781.csv"

            row_values = list(make_archive_row().values())[:-1]

            with file_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(ARCHIVE_HEADER)
                writer.writerow(row_values)

            statistics = make_statistics()
            process_file(file_path, statistics)

            self.assertEqual(statistics["total_rows"], 1)
            self.assertEqual(statistics["valid_rows"], 0)
            self.assertEqual(statistics["invalid_rows"], 1)
            self.assertEqual(
                statistics["errors"]["malformed_row"],
                1,
            )


if __name__ == "__main__":
    unittest.main()
