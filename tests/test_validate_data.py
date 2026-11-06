
import unittest
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

from src.validate_data import (
    validate_numeric_field,
    validate_date,
    validate_time,
    validate_categorical_field,
    validate_row,
    process_file,
)


class TestNumericValidation(unittest.TestCase):

    def test_valid_coordinates(self):
        self.assertIsNone(validate_numeric_field("latitude", "42.5"))
        self.assertIsNone(validate_numeric_field("longitude", "-3.7"))

    def test_invalid_coordinates(self):
        self.assertEqual(
            validate_numeric_field("latitude", "95"),
            "out_of_range"
        )
        self.assertEqual(
            validate_numeric_field("longitude", "-200"),
            "out_of_range"
        )

    def test_missing_numeric_value(self):
        self.assertEqual(
            validate_numeric_field("frp", ""),
            "missing"
        )

    def test_negative_frp(self):
        self.assertEqual(
            validate_numeric_field("frp", "-10"),
            "out_of_range"
        )


class TestDateValidation(unittest.TestCase):

    def test_valid_date(self):
        self.assertIsNone(validate_date("2026-11-06"))

    def test_invalid_date(self):
        self.assertEqual(validate_date("2026-02-30"), "invalid_date")


class TestTimeValidation(unittest.TestCase):

    def test_valid_time(self):
        self.assertIsNone(validate_time("0830"))
        self.assertIsNone(validate_time("0005"))

    def test_invalid_time(self):
        self.assertEqual(validate_time("2560"), "invalid_time")
        self.assertEqual(validate_time("930"), "invalid_time")


class TestCategoricalValidation(unittest.TestCase):

    def test_modis_confidence(self):
        self.assertIsNone(
            validate_categorical_field("confidence", "85", "MODIS")
        )

    def test_invalid_modis_confidence(self):
        self.assertEqual(
            validate_categorical_field("confidence", "120", "MODIS"),
            "out_of_range"
        )

    def test_viirs_confidence(self):
        self.assertIsNone(
            validate_categorical_field("confidence", "h", "VIIRS")
        )

    def test_invalid_viirs_confidence(self):
        self.assertEqual(
            validate_categorical_field("confidence", "85", "VIIRS"),
            "invalid_category"
        )


class TestRowValidation(unittest.TestCase):

    def test_valid_modis_row(self):
        row = {
            "latitude": "42.5",
            "longitude": "-3.7",
            "brightness": "320.5",
            "scan": "1.0",
            "track": "1.0",
            "bright_t31": "290.0",
            "frp": "12.5",
            "acq_date": "2026-11-06",
            "acq_time": "0830",
            "confidence": "85",
            "daynight": "D",
            "type": "0",
        }

        self.assertEqual(validate_row(row, "MODIS"), [])

    def test_valid_viirs_row(self):
        row = {
            "latitude": "42.5",
            "longitude": "-3.7",
            "brightness": "320.5",
            "scan": "0.4",
            "track": "0.4",
            "bright_t31": "290.0",
            "frp": "12.5",
            "acq_date": "2026-11-06",
            "acq_time": "0830",
            "confidence": "h",
            "daynight": "N",
        }

        self.assertEqual(validate_row(row, "VIIRS"), [])


class TestProcessingStatistics(unittest.TestCase):

    def test_valid_and_invalid_rows_are_counted_correctly(self):

        statistics = {
            "total_rows": 0,
            "valid_rows": 0,
            "invalid_rows": 0,
            "files_processed": 0,
            "errors": Counter(),
        }

        header = (
            "latitude,longitude,brightness,scan,track,acq_date,"
            "acq_time,satellite,instrument,confidence,version,"
            "bright_t31,frp,daynight,type\n"
        )

        valid_row = (
            "42.5,-3.7,320.5,1.0,1.0,2026-11-06,0830,"
            "Terra,MODIS,85,6.1,290.0,12.5,D,0\n"
        )

        invalid_row = (
            "42.5,-3.7,320.5,1.0,1.0,2026-11-06,0830,"
            "Terra,MODIS,85,6.1,290.0,-10,D,0\n"
        )

        with TemporaryDirectory() as temp_dir:

            folder = Path(temp_dir) / "region_modis"
            folder.mkdir()

            file_path = folder / "fire_archive_test.csv"

            file_path.write_text(
                header + valid_row + invalid_row,
                encoding="utf-8"
            )

            process_file(file_path, statistics)

        self.assertEqual(statistics["total_rows"], 2)
        self.assertEqual(statistics["valid_rows"], 1)
        self.assertEqual(statistics["invalid_rows"], 1)
        self.assertEqual(statistics["files_processed"], 1)

        self.assertEqual(
            statistics["errors"]["frp:out_of_range"],
            1
        )

        self.assertEqual(
            statistics["valid_rows"] + statistics["invalid_rows"],
            statistics["total_rows"]
        )


if __name__ == "__main__":
    unittest.main()
