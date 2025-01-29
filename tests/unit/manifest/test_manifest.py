from pathlib import Path
from unittest import TestCase

from ledgered.manifest.manifest import Manifest, MANIFEST_FILE_NAME, TestsConfig

from .. import TEST_MANIFEST_DIRECTORY


class TestManifest(TestCase):
    def check_ledger_app_toml(self, manifest: Manifest) -> None:
        self.assertEqual(manifest.app.sdk, "rust")
        self.assertEqual(manifest.app.devices, {"nanos", "stax", "flex"})
        self.assertEqual(manifest.app.build_directory, Path(""))
        self.assertTrue(manifest.app.is_rust)
        self.assertFalse(manifest.app.is_c)

        self.assertIsInstance(manifest.tests, TestsConfig)
        self.assertEqual(manifest.tests.unit_directory, Path("unit"))
        self.assertEqual(manifest.tests.pytest_directory, Path("pytest"))

    def test___init__ok(self):
        app = {"sdk": "rust", "devices": ["NANOS", "stAX", "flex"], "build_directory": ""}
        tests = {"unit_directory": "unit", "pytest_directory": "pytest"}
        self.check_ledger_app_toml(Manifest(app, tests))

    def test_from_path_ok(self):
        self.check_ledger_app_toml(Manifest.from_path(TEST_MANIFEST_DIRECTORY))
        self.check_ledger_app_toml(Manifest.from_path(TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME))

    def test_from_path_nok(self):
        with self.assertRaises(AssertionError):
            Manifest.from_path(Path("/not/existing/path"))

    def test_from_io_ok(self):
        with (TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME).open() as manifest_io:
            self.check_ledger_app_toml(Manifest.from_io(manifest_io))

    def test_from_string_ok(self):
        with (TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME).open() as manifest_io:
            self.check_ledger_app_toml(Manifest.from_string(manifest_io.read()))

    def test_check_ok(self):
        Manifest.from_path(TEST_MANIFEST_DIRECTORY).check(TEST_MANIFEST_DIRECTORY)

    def test_check_nok(self):
        with self.assertRaises(AssertionError):
            Manifest.from_path(TEST_MANIFEST_DIRECTORY).check("wrong_directory")
