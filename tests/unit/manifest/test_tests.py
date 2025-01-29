from pathlib import Path
from unittest import TestCase

from ledgered.manifest.constants import DEFAULT_USE_CASE
from ledgered.manifest.errors import MissingField
from ledgered.manifest.tests import (
    DuplicateDependencyError,
    TestsConfig,
    TestsDependencyConfig,
    TestsDependenciesConfig,
    APPLICATION_DIRECTORY_KEY,
    APPLICATION_DIRECTORY_NAME,
)


class TestTestsDependencyConfig(TestCase):
    def setUp(self):
        self.n, self.r, self.bd, self.uc = "name", "ref", Path("base_dir"), "use_case"
        self.url = "/".join(["some url", self.n])
        self.tdc = TestsDependencyConfig(self.url, self.r, self.bd, self.uc)

    def test___init__full(self):
        self.assertEqual(self.tdc.url, self.url)
        self.assertEqual(self.tdc.ref, self.r)
        self.assertEqual(self.tdc.use_case, self.uc)
        self.assertEqual(self.tdc._name, self.n)
        self.assertEqual(self.tdc._base_dir, self.bd)

    def test___init__partial(self):
        tdc = TestsDependencyConfig(self.url, self.r, base_dir=self.bd)
        self.assertEqual(tdc.url, self.url)
        self.assertEqual(tdc.ref, self.r)
        self.assertEqual(self.tdc._name, self.n)
        self.assertEqual(self.tdc._base_dir, self.bd)
        self.assertEqual(tdc.use_case, DEFAULT_USE_CASE)

    def test_dir(self):
        path = self.bd / APPLICATION_DIRECTORY_NAME / f"{self.n}-{self.r}-{self.uc}"
        self.assertEqual(self.tdc.dir, path)

    def test___eq__(self):
        self.assertNotEqual(self.tdc, str)
        self.assertEqual(self.tdc, TestsDependencyConfig(self.url, self.r, self.bd, self.uc))
        self.assertNotEqual(self.tdc, TestsDependencyConfig(self.url, self.r, self.bd))

    def test__hash__(self):
        self.assertEqual(hash(self.tdc), hash((self.url, self.r, self.uc)))


class TestTestsDependenciesConfig(TestCase):
    def setUp(self):
        self.bd = Path("test")
        self.u1, self.r1, self.uc1 = "url1", "ref1", "use_case1"
        self.u2, self.r2, self.uc2 = "url2", "ref2", "use_case2"
        self.input = [
            {"url": self.u1, "ref": self.r1, "use_case": self.uc1},
            {"url": self.u2, "ref": self.r2, "use_case": self.uc2},
        ]
        self.tdc = TestsDependenciesConfig(self.input, self.bd)

    def test___init__ok(self):
        self.assertSetEqual(
            self.tdc.dependencies,
            {
                TestsDependencyConfig(self.u1, self.r1, self.bd, self.uc1),
                TestsDependencyConfig(self.u2, self.r2, self.bd, self.uc2),
            },
        )

    def test___init__nok(self):
        with self.assertRaises(DuplicateDependencyError):
            TestsDependenciesConfig(
                [{"url": self.u1, "ref": self.r1, "use_case": self.uc1}] * 2, base_dir="something"
            )

    def test_json(self):
        self.input[0][APPLICATION_DIRECTORY_KEY] = str(
            self.bd / APPLICATION_DIRECTORY_NAME / f"{self.u1}-{self.r1}-{self.uc1}"
        )
        self.input[1][APPLICATION_DIRECTORY_KEY] = str(
            self.bd / APPLICATION_DIRECTORY_NAME / f"{self.u2}-{self.r2}-{self.uc2}"
        )
        # CountEqual rather than ListEqual, as the list is managed as a set and the content can
        # be reordered when serialized back to list
        self.assertCountEqual(self.tdc.json, self.input)


class TestTestsConfig(TestCase):
    maxDiff = None

    def test____init___ok_complete(self):
        ud = Path("")
        pd = Path("something")
        deps = {
            "first": [{"url": "url", "ref": "ref"}],
            "second": [
                {"url": "u1", "ref": "r1", "use_case": "uc1"},
                {"url": "u2", "ref": "r2", "use_case": "uc2"},
            ],
        }
        config = TestsConfig(unit_directory=str(ud), pytest_directory=str(pd), dependencies=deps)
        self.assertIsNotNone(config.unit_directory)
        self.assertEqual(config.unit_directory, ud)
        self.assertIsNotNone(config.pytest_directory)
        self.assertEqual(config.pytest_directory, pd)

        # package automatically replaces empty use_cases with the default one
        deps["first"][0]["use_case"] = DEFAULT_USE_CASE
        # we need to remove and check the dependencies on their own, as they contain lists,
        # which can be reorganized in the package (they are managed as set)
        result_json = config.json
        result_deps = result_json.pop("dependencies")
        self.assertEqual(len(result_deps), len(deps))
        deps["first"][0][APPLICATION_DIRECTORY_KEY] = str(
            pd / APPLICATION_DIRECTORY_NAME / "url-ref-default"
        )
        deps["second"][0][APPLICATION_DIRECTORY_KEY] = str(
            pd / APPLICATION_DIRECTORY_NAME / "u1-r1-uc1"
        )
        deps["second"][1][APPLICATION_DIRECTORY_KEY] = str(
            pd / APPLICATION_DIRECTORY_NAME / "u2-r2-uc2"
        )
        for k, v in result_deps.items():
            self.assertIn(k, deps)
            self.assertCountEqual(v, deps[k])

        # the rest of the json can be compared
        self.assertDictEqual(result_json, {"unit_directory": str(ud), "pytest_directory": str(pd)})

    def test___init___nok_empty(self):
        config = TestsConfig(**dict())
        self.assertIsNone(config.unit_directory)
        self.assertIsNone(config.pytest_directory)
        self.assertIsNone(config.dependencies)

    def test___init__missing_field(self):
        with self.assertRaises(MissingField):
            TestsConfig(dependencies="something")
