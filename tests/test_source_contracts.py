
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.source_contracts import (
    ARCHIVE_HEADER,
    NRT_HEADER,
    identify_source_contract,
    identify_platform,
    read_source_header,
    validate_source_header,
    validate_source_identity,
)


class TestSourceIdentification(unittest.TestCase):

    def test_modis_archive_contract(self):
        path = Path("angola_modis/fire_archive_M-C61_838781.csv")
        contract = identify_source_contract(path)

        self.assertEqual(contract.region_id, "angola")
        self.assertEqual(contract.sensor, "MODIS")
        self.assertEqual(contract.platform_group, "MODIS")
        self.assertEqual(contract.product_token, "M-C61")
        self.assertEqual(contract.collection, "MODIS_C61")
        self.assertEqual(contract.processing_stream, "ARCHIVE")

    def test_modis_nrt_contract(self):
        path = Path("espana_modis/fire_nrt_M-C61_838802.csv")
        contract = identify_source_contract(path)

        self.assertEqual(contract.processing_stream, "NRT")
        self.assertEqual(contract.expected_header, NRT_HEADER)

    def test_viirs_snpp_contract(self):
        path = Path("angola_viirs_snpp/fire_archive_SV-C2_838784.csv")
        contract = identify_source_contract(path)

        self.assertEqual(contract.sensor, "VIIRS")
        self.assertEqual(contract.platform_group, "SNPP")
        self.assertEqual(contract.collection, "VIIRS_C2")

    def test_viirs_noaa20_contract(self):
        path = Path("angola_viirs_20/fire_archive_J1V-C2_838782.csv")
        contract = identify_source_contract(path)

        self.assertEqual(contract.sensor, "VIIRS")
        self.assertEqual(contract.platform_group, "NOAA-20")

    def test_viirs_noaa21_contract(self):
        path = Path("angola_viirs_21/fire_archive_J2V-C2_838783.csv")
        contract = identify_source_contract(path)

        self.assertEqual(contract.sensor, "VIIRS")
        self.assertEqual(contract.platform_group, "NOAA-21")

    def test_archive_provider(self):
        contract = identify_source_contract(
            Path("angola_modis/fire_archive_M-C61_838781.csv")
        )

        self.assertEqual(
            contract.processing_provider,
            "UNIVERSITY_OF_MARYLAND",
        )

    def test_nrt_provider(self):
        contract = identify_source_contract(
            Path("angola_modis/fire_nrt_M-C61_838781.csv")
        )

        self.assertEqual(
            contract.processing_provider,
            "NASA_LANCE_FIRMS",
        )

    def test_rejects_unknown_region(self):
        with self.assertRaises(ValueError):
            identify_source_contract(
                Path("unknown_modis/fire_archive_M-C61_123456.csv")
            )

    def test_rejects_unknown_folder(self):
        with self.assertRaises(ValueError):
            identify_source_contract(
                Path("angola_unknown/fire_archive_M-C61_123456.csv")
            )

    def test_rejects_folder_filename_sensor_mismatch(self):
        with self.assertRaises(ValueError):
            identify_source_contract(
                Path("angola_viirs_20/fire_archive_J2V-C2_838782.csv")
            )

    def test_rejects_unknown_filename_token(self):
        with self.assertRaises(ValueError):
            identify_source_contract(
                Path("angola_modis/fire_archive_X-C2_838781.csv")
            )

    def test_rejects_unrecognised_filename(self):
        with self.assertRaises(ValueError):
            identify_source_contract(
                Path("angola_modis/unknown_file.csv")
            )


class TestPlatformIdentification(unittest.TestCase):

    def test_satellite_platform_mapping(self):
        expected = {
            "Terra": "TERRA",
            "Aqua": "AQUA",
            "SNPP": "SNPP",
            "N20": "NOAA-20",
            "N21": "NOAA-21",
        }

        for raw, canonical in expected.items():
            with self.subTest(raw=raw):
                self.assertEqual(
                    identify_platform(raw),
                    canonical,
                )

    def test_platform_mapping_is_case_insensitive(self):
        self.assertEqual(identify_platform("terra"), "TERRA")
        self.assertEqual(identify_platform("n20"), "NOAA-20")

    def test_rejects_unknown_platform(self):
        with self.assertRaises(ValueError):
            identify_platform("NOAA-19")

    def test_rejects_missing_platform(self):
        with self.assertRaises(ValueError):
            identify_platform(None)

    def test_modis_accepts_terra(self):
        contract = identify_source_contract(
            Path("angola_modis/fire_archive_M-C61_838781.csv")
        )

        self.assertEqual(
            validate_source_identity(contract, "Terra", "MODIS"),
            "TERRA",
        )

    def test_modis_accepts_aqua(self):
        contract = identify_source_contract(
            Path("angola_modis/fire_archive_M-C61_838781.csv")
        )

        self.assertEqual(
            validate_source_identity(contract, "Aqua", "MODIS"),
            "AQUA",
        )

    def test_noaa20_requires_viirs_instrument(self):
        contract = identify_source_contract(
            Path("angola_viirs_20/fire_archive_J1V-C2_838782.csv")
        )

        with self.assertRaises(ValueError):
            validate_source_identity(contract, "N20", "SNPP")

    def test_snpp_requires_snpp_instrument(self):
        contract = identify_source_contract(
            Path("angola_viirs_snpp/fire_archive_SV-C2_838784.csv")
        )

        with self.assertRaises(ValueError):
            validate_source_identity(contract, "SNPP", "VIIRS")

    def test_rejects_platform_folder_mismatch(self):
        contract = identify_source_contract(
            Path("angola_viirs_20/fire_archive_J1V-C2_838782.csv")
        )

        with self.assertRaises(ValueError):
            validate_source_identity(contract, "N21", "VIIRS")

    def test_rejects_missing_satellite(self):
        contract = identify_source_contract(
            Path("angola_modis/fire_archive_M-C61_838781.csv")
        )

        with self.assertRaises(ValueError):
            validate_source_identity(contract, None, "MODIS")

    def test_rejects_missing_instrument(self):
        contract = identify_source_contract(
            Path("angola_modis/fire_archive_M-C61_838781.csv")
        )

        with self.assertRaises(ValueError):
            validate_source_identity(contract, "Terra", None)


class TestHeaderValidation(unittest.TestCase):

    def test_archive_header_constant(self):
        self.assertEqual(len(ARCHIVE_HEADER), 15)
        self.assertEqual(ARCHIVE_HEADER[-1], "type")

    def test_nrt_header_constant(self):
        self.assertEqual(len(NRT_HEADER), 14)
        self.assertNotIn("type", NRT_HEADER)

    def test_accepts_exact_archive_header(self):
        with TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "angola_modis"
            folder.mkdir()

            path = folder / "fire_archive_M-C61_838781.csv"
            path.write_text(
                ",".join(ARCHIVE_HEADER) + "\n",
                encoding="utf-8",
            )

            self.assertEqual(
                validate_source_header(path),
                ARCHIVE_HEADER,
            )

    def test_accepts_exact_nrt_header(self):
        with TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "angola_modis"
            folder.mkdir()

            path = folder / "fire_nrt_M-C61_838781.csv"
            path.write_text(
                ",".join(NRT_HEADER) + "\n",
                encoding="utf-8",
            )

            self.assertEqual(
                validate_source_header(path),
                NRT_HEADER,
            )

    def test_rejects_reordered_columns(self):
        with TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "angola_modis"
            folder.mkdir()

            path = folder / "fire_archive_M-C61_838781.csv"
            reordered = list(ARCHIVE_HEADER)
            reordered[0], reordered[1] = (
                reordered[1],
                reordered[0],
            )

            path.write_text(
                ",".join(reordered) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                validate_source_header(path)

    def test_rejects_type_in_nrt(self):
        with TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "angola_modis"
            folder.mkdir()

            path = folder / "fire_nrt_M-C61_838781.csv"
            path.write_text(
                ",".join(ARCHIVE_HEADER) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                validate_source_header(path)

    def test_rejects_duplicate_columns(self):
        with TemporaryDirectory() as temp_dir:
            folder = Path(temp_dir) / "angola_modis"
            folder.mkdir()

            path = folder / "fire_archive_M-C61_838781.csv"
            duplicate = list(ARCHIVE_HEADER)
            duplicate[-1] = duplicate[0]

            path.write_text(
                ",".join(duplicate) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                read_source_header(path)

    def test_rejects_empty_file(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "empty.csv"
            path.write_text("", encoding="utf-8")

            with self.assertRaises(ValueError):
                read_source_header(path)


if __name__ == "__main__":
    unittest.main()
