from unittest import TestCase

from ledgered.manifest.constants import DEFAULT_USE_CASE
from ledgered.manifest.use_cases import UseCasesConfig


class TestUseCaseConfig(TestCase):
    def setUp(self):
        self.key = "first"
        self.cases = {self.key: "something", "other": "something else"}
        self.uc = UseCasesConfig(**self.cases)

    def test___init__empty(self):
        uc = UseCasesConfig()
        self.assertEqual(uc.cases, dict())

    def test___init__ok(self):
        self.assertEqual(self.uc.cases, self.cases)

    def test___init__nok(self):
        with self.assertRaises(ValueError):
            UseCasesConfig(default="something")
        with self.assertRaises(ValueError):
            UseCasesConfig(case=3)

    def test_json(self):
        self.assertEqual(self.uc.json, self.cases)

    def test_get_ok(self):
        self.assertEqual(self.uc.get(self.key), self.cases[self.key])

    def test_get_default(self):
        self.assertEqual(self.uc.get(DEFAULT_USE_CASE), str())

    def test_get_nok(self):
        with self.assertRaises(KeyError):
            self.uc.get("does not exist")
