import json
import tempfile
from dataclasses import dataclass
from unittest import TestCase
from unittest.mock import patch
from pathlib import Path
from typing import Any

from ledgered import binary as B


class TestSections(TestCase):
    def setUp(self):
        self.inputs = {
            "api_level": "api_level",
            "app_name": "app_name",
            "app_version": "app_version",
            "rust_sdk_name": None,
            "rust_sdk_version": None,
            "sdk_graphics": "sdk_graphics",
            "sdk_hash": "sdk_hash",
            "sdk_name": "sdk_name",
            "sdk_version": "sdk_version",
            "target": "target",
            "target_id": "target_id",
            "target_name": "target_name",
            "target_version": "target_version",
            "app_flags": "app_flags",
        }

    def test___init__empty(self):
        sections = B.Sections()
        self.assertIsNone(sections.api_level)
        self.assertIsNone(sections.app_name)
        self.assertIsNone(sections.app_version)
        self.assertIsNone(sections.rust_sdk_name)
        self.assertIsNone(sections.rust_sdk_version)
        self.assertEqual(sections.sdk_graphics, B.DEFAULT_GRAPHICS)
        self.assertIsNone(sections.sdk_hash)
        self.assertIsNone(sections.sdk_name)
        self.assertIsNone(sections.sdk_version)
        self.assertIsNone(sections.target)
        self.assertIsNone(sections.target_id)
        self.assertIsNone(sections.target_name)
        self.assertIsNone(sections.target_version)
        self.assertIsNone(sections.app_flags)

    def test___str__(self):
        sections = B.Sections(**self.inputs)
        self.assertEqual(
            "\n".join(f"{k} {v}" for k, v in sorted(self.inputs.items())), str(sections)
        )

    def test_json(self):
        sections = B.Sections(**self.inputs)
        # explicit `str(v)` as None values needs to be converted to 'None'
        self.assertDictEqual({k: str(v) for k, v in self.inputs.items()}, sections.json)


@dataclass
class Section:
    name: str
    _data: Any

    def data(self) -> Any:
        return self._data


class TestLedgerBinaryApp(TestCase):
    def test___init__(self):
        path = Path("/dev/urandom")
        api_level, sdk_hash = "something", "some hash"
        expected = B.Sections(api_level=api_level, sdk_hash=sdk_hash)
        with patch("ledgered.binary.ELFFile") as elfmock:
            elfmock().iter_sections.return_value = [
                Section("unused", 1),
                Section("ledger.api_level", api_level.encode()),
                Section("ledger.sdk_hash", sdk_hash.encode()),
                Section("still not used", b"some data"),
            ]
            bin = B.LedgerBinaryApp(path)
        self.assertEqual(bin.sections, expected)

    def test___init__from_str(self):
        path = "/dev/urandom"
        with patch("ledgered.binary.ELFFile"):
            B.LedgerBinaryApp(path)

    def test_c_app_detection(self):
        """Test that C apps are correctly identified (no rust SDK fields)."""
        path = Path("/dev/urandom")
        with patch("ledgered.binary.ELFFile") as elfmock:
            elfmock().iter_sections.return_value = [
                Section("ledger.app_name", b"Test App"),
                Section("ledger.app_version", b"1.0.0"),
                Section("ledger.target", b"stax"),
            ]
            bin = B.LedgerBinaryApp(path)

        self.assertFalse(bin.is_rust_app)
        self.assertEqual(bin.sections.app_name, "Test App")
        self.assertEqual(bin.sections.app_version, "1.0.0")

    def test_rust_app_detection(self):
        """Test that Rust apps are correctly identified by rust_sdk_name."""
        path = Path("/dev/urandom")
        with patch("ledgered.binary.ELFFile") as elfmock:
            elfmock().iter_sections.return_value = [
                Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
                Section("ledger.target", b"flex"),
            ]
            bin = B.LedgerBinaryApp(path)

        self.assertTrue(bin.is_rust_app)

    def test_rust_app_detection_by_version(self):
        """Test that Rust apps are correctly identified by rust_sdk_version."""
        path = Path("/dev/urandom")
        with patch("ledgered.binary.ELFFile") as elfmock:
            elfmock().iter_sections.return_value = [
                Section("ledger.rust_sdk_version", b"1.12.0"),
                Section("ledger.target", b"stax"),
            ]
            bin = B.LedgerBinaryApp(path)

        self.assertTrue(bin.is_rust_app)

    def test_rust_app_loads_metadata_from_json(self):
        """Test that Rust apps load app_name, app_version, and app_flags from JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            binary_path = tmpdir_path / "app-boilerplate-rust"
            binary_path.touch()

            # Create companion JSON file
            json_data = {
                "name": "Rust Boilerplate",
                "version": "1.7.7",
                "flags": "0x200",
                "apiLevel": "25",
                "targetId": "0x33300004",
            }
            json_path = tmpdir_path / "app_flex.json"
            with json_path.open("w") as f:
                json.dump(json_data, f)

            with patch("ledgered.binary.ELFFile") as elfmock:
                elfmock().iter_sections.return_value = [
                    Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
                    Section("ledger.rust_sdk_version", b"1.12.0"),
                    Section("ledger.target", b"flex"),
                    Section("ledger.api_level", b"25"),
                ]
                bin = B.LedgerBinaryApp(binary_path)

            self.assertTrue(bin.is_rust_app)
            self.assertEqual(bin.sections.app_name, "Rust Boilerplate")
            self.assertEqual(bin.sections.app_version, "1.7.7")
            self.assertEqual(bin.sections.app_flags, "0x200")
            self.assertEqual(bin.sections.api_level, "25")

    def test_rust_app_missing_json_file(self):
        """Test that Rust apps handle missing JSON file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            binary_path = tmpdir_path / "app-boilerplate-rust"
            binary_path.touch()

            # No JSON file created
            with patch("ledgered.binary.ELFFile") as elfmock:
                elfmock().iter_sections.return_value = [
                    Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
                    Section("ledger.target", b"flex"),
                ]
                with patch("ledgered.binary.logging") as log_mock:
                    bin = B.LedgerBinaryApp(binary_path)

                # Should warn about missing JSON
                log_mock.warning.assert_called()

            self.assertTrue(bin.is_rust_app)
            self.assertIsNone(bin.sections.app_name)
            self.assertIsNone(bin.sections.app_version)

    def test_rust_app_no_target(self):
        """Test that Rust apps without target field handle JSON loading gracefully."""
        path = Path("/dev/urandom")
        with patch("ledgered.binary.ELFFile") as elfmock:
            elfmock().iter_sections.return_value = [
                Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
            ]
            with patch("ledgered.binary.logging") as log_mock:
                bin = B.LedgerBinaryApp(path)

            # Should warn about missing target
            log_mock.warning.assert_called()

        self.assertTrue(bin.is_rust_app)
        self.assertIsNone(bin.sections.app_name)

    def test_rust_app_malformed_json(self):
        """Test that Rust apps handle malformed JSON gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            binary_path = tmpdir_path / "app-boilerplate-rust"
            binary_path.touch()

            # Create malformed JSON file
            json_path = tmpdir_path / "app_flex.json"
            with json_path.open("w") as f:
                f.write("{ this is not valid json }")

            with patch("ledgered.binary.ELFFile") as elfmock:
                elfmock().iter_sections.return_value = [
                    Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
                    Section("ledger.target", b"flex"),
                ]
                with patch("ledgered.binary.logging") as log_mock:
                    bin = B.LedgerBinaryApp(binary_path)

                # Should log error
                log_mock.error.assert_called()

            self.assertTrue(bin.is_rust_app)
            self.assertIsNone(bin.sections.app_name)

    def test_rust_app_partial_json_data(self):
        """Test that Rust apps handle JSON with missing fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            binary_path = tmpdir_path / "app-boilerplate-rust"
            binary_path.touch()

            # Create JSON file with only some fields
            json_data = {
                "name": "Rust App",
                # Missing version and flags
            }
            json_path = tmpdir_path / "app_stax.json"
            with json_path.open("w") as f:
                json.dump(json_data, f)

            with patch("ledgered.binary.ELFFile") as elfmock:
                elfmock().iter_sections.return_value = [
                    Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
                    Section("ledger.target", b"stax"),
                ]
                bin = B.LedgerBinaryApp(binary_path)

            self.assertTrue(bin.is_rust_app)
            self.assertEqual(bin.sections.app_name, "Rust App")
            self.assertIsNone(bin.sections.app_version)
            self.assertIsNone(bin.sections.app_flags)

    def test_c_app_does_not_load_json(self):
        """Test that C apps do not attempt to load JSON file even if present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            binary_path = tmpdir_path / "app.elf"
            binary_path.touch()

            # Create JSON file that should be ignored
            json_data = {
                "name": "Should Be Ignored",
                "version": "9.9.9",
            }
            json_path = tmpdir_path / "app_stax.json"
            with json_path.open("w") as f:
                json.dump(json_data, f)

            with patch("ledgered.binary.ELFFile") as elfmock:
                elfmock().iter_sections.return_value = [
                    Section("ledger.app_name", b"C App"),
                    Section("ledger.app_version", b"1.0.0"),
                    Section("ledger.target", b"stax"),
                ]
                bin = B.LedgerBinaryApp(binary_path)

            # Should use ELF data, not JSON
            self.assertFalse(bin.is_rust_app)
            self.assertEqual(bin.sections.app_name, "C App")
            self.assertEqual(bin.sections.app_version, "1.0.0")

    def test_rust_app_device_name_mapping_nanos2_to_nanosplus(self):
        """Test that nanos2 target maps to app_nanosplus.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            binary_path = tmpdir_path / "app-boilerplate-rust"
            binary_path.touch()

            # Create JSON with normalized name
            json_data = {
                "name": "NanoS+ App",
                "version": "1.0.0",
                "flags": "0x200",
            }
            json_path = tmpdir_path / "app_nanosp.json"
            with json_path.open("w") as f:
                json.dump(json_data, f)

            with patch("ledgered.binary.ELFFile") as elfmock:
                elfmock().iter_sections.return_value = [
                    Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
                    Section("ledger.target", b"nanos2"),  # ELF says nanos2
                ]
                bin = B.LedgerBinaryApp(binary_path)

            # Should successfully load from app_nanosp.json
            self.assertTrue(bin.is_rust_app)
            self.assertEqual(bin.sections.app_name, "NanoS+ App")
            self.assertEqual(bin.sections.app_version, "1.0.0")

    def test_rust_app_device_name_mapping_nanosplus_to_nanosplus(self):
        """Test that nanosplus target maps to app_nanosplus.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            binary_path = tmpdir_path / "app-boilerplate-rust"
            binary_path.touch()

            # Create JSON with normalized name
            json_data = {
                "name": "NanoS+ App",
                "version": "2.0.0",
            }
            json_path = tmpdir_path / "app_nanosp.json"
            with json_path.open("w") as f:
                json.dump(json_data, f)

            with patch("ledgered.binary.ELFFile") as elfmock:
                elfmock().iter_sections.return_value = [
                    Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
                    Section("ledger.target", b"nanosplus"),  # ELF says nanosplus
                ]
                bin = B.LedgerBinaryApp(binary_path)

            # Should successfully load from app_nanosp.json
            self.assertTrue(bin.is_rust_app)
            self.assertEqual(bin.sections.app_name, "NanoS+ App")
            self.assertEqual(bin.sections.app_version, "2.0.0")

    def test_rust_app_device_name_mapping_nanos_plus_to_nanosplus(self):
        """Test that nanos+ target maps to app_nanosplus.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            binary_path = tmpdir_path / "app-boilerplate-rust"
            binary_path.touch()

            # Create JSON with normalized name
            json_data = {
                "name": "NanoS+ App",
                "version": "3.0.0",
            }
            json_path = tmpdir_path / "app_nanosp.json"
            with json_path.open("w") as f:
                json.dump(json_data, f)

            with patch("ledgered.binary.ELFFile") as elfmock:
                elfmock().iter_sections.return_value = [
                    Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
                    Section("ledger.target", b"nanos+"),  # ELF says nanos+
                ]
                bin = B.LedgerBinaryApp(binary_path)

            # Should successfully load from app_nanosp.json
            self.assertTrue(bin.is_rust_app)
            self.assertEqual(bin.sections.app_name, "NanoS+ App")
            self.assertEqual(bin.sections.app_version, "3.0.0")

    def test_rust_app_unknown_device_fallback(self):
        """Test that unknown device names fallback to using the original target name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            binary_path = tmpdir_path / "app-boilerplate-rust"
            binary_path.touch()

            # Create JSON with the unknown device name
            json_data = {
                "name": "Future Device App",
                "version": "1.0.0",
            }
            json_path = tmpdir_path / "app_futuredevice.json"
            with json_path.open("w") as f:
                json.dump(json_data, f)

            with patch("ledgered.binary.ELFFile") as elfmock:
                elfmock().iter_sections.return_value = [
                    Section("ledger.rust_sdk_name", b"ledger_secure_sdk_sys"),
                    Section("ledger.target", b"futuredevice"),  # Unknown device
                ]
                bin = B.LedgerBinaryApp(binary_path)

            # Should use original name and successfully load
            self.assertTrue(bin.is_rust_app)
            self.assertEqual(bin.sections.app_name, "Future Device App")
            self.assertEqual(bin.sections.app_version, "1.0.0")
