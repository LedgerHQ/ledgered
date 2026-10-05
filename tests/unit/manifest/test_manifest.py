from pathlib import Path
from unittest import TestCase

from ledgered.manifest.manifest import MANIFEST_FILE_NAME, Manifest, PyTestsConfig, TestsConfig, UnitTestsConfig

from .. import TEST_MANIFEST_DIRECTORY


class TestManifest(TestCase):
    def check_ledger_app_toml(self, manifest: Manifest) -> None:
        self.assertEqual(manifest.app.sdk, "rust")
        self.assertEqual(manifest.app.devices, {"nanos", "stax", "flex"})
        self.assertEqual(manifest.app.build_directory, Path(""))
        self.assertTrue(manifest.app.is_rust)
        self.assertFalse(manifest.app.is_c)

        self.assertIsInstance(manifest.pytests[0], TestsConfig)
        assert isinstance(manifest.pytests[0], TestsConfig)
        self.assertEqual(manifest.pytests[0].unit_directory, Path("unit"))
        self.assertEqual(manifest.pytests[0].pytest_directory, Path("pytest"))

    def test___init__ok(self):
        app = {"sdk": "rust", "devices": ["NANOS", "stAX", "flex"], "build_directory": ""}
        tests = {"unit_directory": "unit", "pytest_directory": "pytest"}
        self.check_ledger_app_toml(Manifest(app, tests))

    def test___init__metadata(self):
        app = {"sdk": "c", "devices": ["flex"], "build_directory": ""}
        metadata = {"author": "Ledger", "contact": "support@ledger.com", "compatible_wallets": ["Ledger Wallet"]}
        manifest = Manifest(app, metadata=metadata)
        assert manifest.metadata is not None
        self.assertEqual(manifest.metadata.author, "Ledger")
        self.assertEqual(manifest.metadata.compatible_wallets, ["Ledger Wallet"])
        self.assertIsNone(Manifest(app).metadata)

    def test___init__pytest_and_unit_tests(self):
        app = {"sdk": "c", "devices": ["nanos"], "build_directory": ""}
        pytest = {"standalone": {"directory": "tests/standalone"}, "swap": {"directory": "tests/swap"}}
        manifest = Manifest(app, pytest=pytest, unit_tests={"directory": "unit"})

        self.assertEqual(len(manifest.pytests), 2)
        for config in manifest.pytests:
            self.assertIsInstance(config, PyTestsConfig)
        assert isinstance(manifest.pytests[0], PyTestsConfig)
        assert isinstance(manifest.pytests[1], PyTestsConfig)
        self.assertEqual(manifest.pytests[0].key, "standalone")
        self.assertEqual(manifest.pytests[1].directory, Path("tests/swap"))
        self.assertIsInstance(manifest.unit_tests, UnitTestsConfig)
        assert manifest.unit_tests is not None
        self.assertEqual(manifest.unit_tests.unit_directory, Path("unit"))

    def test___init__no_tests(self):
        manifest = Manifest({"sdk": "c", "devices": ["nanos"], "build_directory": ""})
        self.assertListEqual(manifest.pytests, [])
        self.assertIsNone(manifest.unit_tests)
        self.assertIsNone(manifest.use_cases)

    def test_from_path_ok(self):
        self.check_ledger_app_toml(Manifest.from_path(TEST_MANIFEST_DIRECTORY))
        self.check_ledger_app_toml(Manifest.from_path(TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME))

    def test_from_path_nok(self):
        with self.assertRaises(AssertionError):
            Manifest.from_path(Path("/not/existing/path"))

    def test_from_io_ok(self):
        with (TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME).open("rb") as manifest_io:
            self.check_ledger_app_toml(Manifest.from_io(manifest_io))

    def test_from_string_ok(self):
        with (TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME).open() as manifest_io:
            self.check_ledger_app_toml(Manifest.from_string(manifest_io.read()))

    def test_check_ok(self):
        Manifest.from_path(TEST_MANIFEST_DIRECTORY).check(TEST_MANIFEST_DIRECTORY)

    def test_check_nok(self):
        with self.assertRaises(AssertionError):
            Manifest.from_path(TEST_MANIFEST_DIRECTORY).check("wrong_directory")
