from pathlib import Path
from unittest import TestCase

from ledgered.manifest.manifest import LegacyManifest, Manifest, RepoManifest, MANIFEST_FILE_NAME


TEST_MANIFEST_DIRECTORY = Path(__file__).parent.parent / "_data"


class DummyRepoManifest(RepoManifest):
    def check(self, directory) -> None:
        pass


class TestRepoManifest(TestCase):

    def test_from_path(self):
        manifest = TEST_MANIFEST_DIRECTORY
        self.assertIsInstance(DummyRepoManifest.from_path(manifest), Manifest)

        manifest = TEST_MANIFEST_DIRECTORY / "ledger_app.toml"
        self.assertIsInstance(DummyRepoManifest.from_path(manifest), Manifest)

        legacy = TEST_MANIFEST_DIRECTORY / "legacy" / "ledger_app.toml"
        self.assertIsInstance(DummyRepoManifest.from_path(legacy), LegacyManifest)

    def test_from_io(self):
        with (TEST_MANIFEST_DIRECTORY / "ledger_app.toml").open() as io:
            self.assertIsInstance(DummyRepoManifest.from_io(io), Manifest)

    def test_from_path_nok(self):
        with self.assertRaises(AssertionError):
            RepoManifest.from_path(Path("/not/existing/path"))


class TestManifest(TestCase):

    def check_ledger_app_toml(self, manifest: Manifest) -> None:
        self.assertEqual(manifest.app.sdk, "rust")
        self.assertEqual(manifest.app.devices, {"nanos", "stax"})
        self.assertEqual(manifest.app.build_directory, Path(""))
        self.assertTrue(manifest.app.is_rust)
        self.assertFalse(manifest.app.is_c)

        self.assertEqual(manifest.tests.unit_directory, Path("unit"))
        self.assertEqual(manifest.tests.pytest_directory, Path("pytest"))

    def test___init__ok(self):
        app = {"sdk": "rust", "devices": ["NANOS", "stAX"], "build_directory": ""}
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


class TestLegacyManifest(TestCase):

    def test___init___ok(self):
        expected = "some expected path"
        manifest = LegacyManifest(**{"rust-app": {"manifest-path": expected}})
        self.assertEqual(manifest.manifest_path, Path(expected))

    def test___init___nok(self):
        with self.assertRaises(ValueError):
            LegacyManifest(wrong_key=4)
        with self.assertRaises(ValueError):
            LegacyManifest(**{"rust-app": {"wrong subkey": 4}})

    def test_from_path_ok(self):
        manifest = LegacyManifest.from_path(TEST_MANIFEST_DIRECTORY / "legacy" / "ledger_app.toml")
        self.assertEqual(manifest.manifest_path, Path("Cargo.toml"))

    def test_from_path_ok2(self):
        manifest = LegacyManifest.from_path(TEST_MANIFEST_DIRECTORY / "legacy")
        self.assertEqual(manifest.manifest_path, Path("Cargo.toml"))

    def test_check_ok(self):
        LegacyManifest.from_path(TEST_MANIFEST_DIRECTORY / "legacy").check(TEST_MANIFEST_DIRECTORY / "legacy")

    def test_check_nok(self):
        with self.assertRaises(AssertionError):
            LegacyManifest.from_path(TEST_MANIFEST_DIRECTORY / "legacy").check("wrong_directory")
