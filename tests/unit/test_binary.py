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
