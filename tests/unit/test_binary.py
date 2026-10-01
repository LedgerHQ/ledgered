import ast
import logging
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any
from unittest import TestCase
from unittest.mock import patch

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
        self.assertEqual("\n".join(f"{k} {v}" for k, v in sorted(self.inputs.items())), str(sections))

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


class TestMain(TestCase):
    def setUp(self):
        self.sections = B.Sections(app_name="some app", api_level="12")
        app_patch = patch("ledgered.binary.LedgerBinaryApp")
        self.app = app_patch.start()
        self.app.return_value.sections = self.sections
        self.addCleanup(app_patch.stop)
        level = logging.root.level
        self.addCleanup(logging.root.setLevel, level)

    def _main(self, *args: str) -> str:
        with patch("sys.argv", ["ledger-binary", *args]), patch("sys.stdout", new_callable=StringIO) as stdout:
            B.main()
        return stdout.getvalue()

    def test_set_parser(self):
        args = B.set_parser().parse_args(["-vv", "-j", "some/file"])
        self.assertEqual(args.verbose, 2)
        self.assertTrue(args.json)
        self.assertEqual(args.binary, Path("some/file"))

    def test_main_text(self):
        with patch.object(Path, "is_file", return_value=True):
            output = self._main("some/file")
        self.assertEqual(output, f"{self.sections}\n")
        self.app.assert_called_once_with(Path("some/file"))

    def test_main_json(self):
        with patch.object(Path, "is_file", return_value=True):
            output = self._main("--json", "some/file")
        # documented as 'JSON-like': a Python dict repr, not strict JSON
        self.assertDictEqual(ast.literal_eval(output), self.sections.json)

    def test_main_verbosity(self):
        for flags, level in [(["-v"], logging.INFO), (["-vv"], logging.DEBUG), (["-vvv"], logging.DEBUG)]:
            with self.subTest(flags=flags), patch.object(Path, "is_file", return_value=True):
                logging.root.setLevel(logging.WARNING)
                self._main(*flags, "some/file")
                self.assertEqual(logging.root.level, level)

    def test_main_not_a_file(self):
        with patch.object(Path, "is_file", return_value=False), self.assertRaises(AssertionError):
            self._main("/not/existing/file")
        self.app.assert_not_called()
