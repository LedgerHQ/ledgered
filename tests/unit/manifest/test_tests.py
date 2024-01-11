from pathlib import Path
from unittest import TestCase

from ledgered.manifest.tests import TestsConfig


class TestTestsConfig(TestCase):

    def test____init___ok_complete(self):
        ud = Path("")
        pd = Path("something")
        config = TestsConfig(unit_directory=str(ud), pytest_directory=str(pd))
        self.assertIsNotNone(config.unit_directory)
        self.assertEqual(config.unit_directory, ud)
        self.assertIsNotNone(config.pytest_directory)
        self.assertEqual(config.pytest_directory, pd)

    def test___init___ok_empty(self):
        config = TestsConfig(**dict())
        self.assertIsNone(config.unit_directory)
        self.assertIsNone(config.pytest_directory)
