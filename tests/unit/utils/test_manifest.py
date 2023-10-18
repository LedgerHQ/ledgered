from pathlib import Path
from unittest import TestCase

from ledgered.utils.manifest import AppConfig, RepoManifest, TestsConfig, MANIFEST_FILE_NAME


TEST_MANIFEST_DIRECTORY = Path(__file__).parent.parent / "_data"


class TestAppConfig(TestCase):

    def test___init__ok_complete(self):
        sdk = "Rust"
        bd = Path("some path")
        devices = ["nanos", "NanoS+"]
        config = AppConfig(sdk=sdk, build_directory=str(bd), devices=devices)
        self.assertEqual(config.sdk, sdk.lower())
        self.assertEqual(config.build_directory, bd)
        self.assertEqual(config.devices, {device.lower() for device in devices})
        self.assertTrue(config.is_rust)
        self.assertFalse(config.is_c)

    def test___init__nok_unknown_sdk(self):
        with self.assertRaises(ValueError):
            AppConfig(sdk="Java", build_directory=str(), devices=set())

    def test___init__nok_unknown_device(self):
        devices = {"hic sunt", "dracones"}
        with self.assertRaises(ValueError) as error:
            AppConfig(sdk="rust", build_directory=str(), devices=devices)
        self.assertIn("', '".join(devices), str(error.exception))


class TestTestsConfig(TestCase):

    def test___init__ok_complete(self):
        ud = Path("")
        pd = Path("something")
        config = TestsConfig(unit_directory=str(ud), pytest_directory=str(pd))
        self.assertIsNotNone(config.unit_directory)
        self.assertEqual(config.unit_directory, ud)
        self.assertIsNotNone(config.pytest_directory)
        self.assertEqual(config.pytest_directory, pd)

    def test__init__ok_empty(self):
        config = TestsConfig(**dict())
        self.assertIsNone(config.unit_directory)
        self.assertIsNone(config.pytest_directory)


class TestRepoManifest(TestCase):

    def check_ledger_app_toml(self, manifest: RepoManifest) -> None:
        self.assertEqual(manifest.app.sdk, "rust")
        self.assertEqual(manifest.app.devices, {"nanos", "stax"})
        self.assertEqual(manifest.app.build_directory, Path())
        self.assertTrue(manifest.app.is_rust)
        self.assertFalse(manifest.app.is_c)

        self.assertEqual(manifest.tests.unit_directory, Path("unit"))
        self.assertEqual(manifest.tests.pytest_directory, Path("pytest"))

    def test___init__ok(self):
        app = {"sdk": "rust", "devices": ["NANOS", "stAX"], "build_directory": ""}
        tests = {"unit_directory": "unit", "pytest_directory": "pytest"}
        self.check_ledger_app_toml(RepoManifest(app, tests))

    def test_from_path_ok(self):
        self.check_ledger_app_toml(RepoManifest.from_path(TEST_MANIFEST_DIRECTORY))
        self.check_ledger_app_toml(RepoManifest.from_path(TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME))

    def test_from_path_nok(self):
        with self.assertRaises(AssertionError):
            RepoManifest.from_path(Path("/not/existing/path"))

    def test_from_io_ok(self):
        with (TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME).open() as manifest_io:
            self.check_ledger_app_toml(RepoManifest.from_io(manifest_io))

    def test_from_string_ok(self):
        with (TEST_MANIFEST_DIRECTORY / MANIFEST_FILE_NAME).open() as manifest_io:
            self.check_ledger_app_toml(RepoManifest.from_string(manifest_io.read()))