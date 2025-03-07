from argparse import ArgumentParser, Namespace
from json import loads
from unittest import TestCase
from unittest.mock import MagicMock, patch

from ledgered.manifest.cli import main, set_parser

from .. import TEST_MANIFEST_DIRECTORY


class PrintMock(MagicMock):
    def get(self):
        result = list()
        for call_args in self.call_args_list:
            result.append(call_args[0][0])
        self.reset_mock()
        return "\n".join(result)


FULL_EXPECTED_TEXT = """build_directory: .
sdk: c
devices:
0. nanox
use_cases:
  debug: DEBUG=1
  test: DEBUG=1
tests:
  unit_directory: tests/unit
  pytest_directory: tests/functional"""

FULL_EXPECTED_JSON = {
    "build_directory": ".",
    "sdk": "c",
    "devices": ["nanox"],
    "use_cases": {"debug": "DEBUG=1", "test": "DEBUG=1"},
    "tests": {"unit_directory": "tests/unit", "pytest_directory": "tests/functional"},
}

UC_D_EXPECTED_TEXT_CHUNKS = [
    """use_cases:
  debug: DEBUG=1
  test: DEBUG=1
tests:
  dependencies:
    testing_develop:""",
    """
      url: https://github.com/<owner>/<app-repository>
      ref: develop
      use_case: debug
      application_directory: tests/functional/.dependencies/<app-repository>-develop-debug""",
    """
      url: https://github.com/<owner>/<other-app-repository>
      ref: develop
      use_case: default
      application_directory: tests/functional/.dependencies/<other-app-repository>-develop-default""",
]

UC_D_EXPECTED_JSON = {
    "use_cases": {"debug": "DEBUG=1", "test": "DEBUG=1"},
    "tests": {"dependencies": {}},
}

EXPECTED_DEPENDENCIES_JSON = [
    {
        "url": "https://github.com/<owner>/<app-repository>",
        "ref": "develop",
        "use_case": "debug",
        "application_directory": "tests/functional/.dependencies/<app-repository>-develop-debug",
    },
    {
        "url": "https://github.com/<owner>/<other-app-repository>",
        "ref": "develop",
        "use_case": "default",
        "application_directory": "tests/functional/.dependencies/<other-app-repository>-develop-default",
    },
]


class TestCLIMain(TestCase):
    diffMax = None

    def setUp(self):
        self.args = Namespace(
            source=TEST_MANIFEST_DIRECTORY / "full_correct.toml",
            check=None,
            verbose=0,
            token=None,
            output_build_directory=False,
            output_sdk=False,
            output_devices=False,
            output_use_cases=None,
            output_tests_unit_directory=False,
            output_tests_pytest_directory=False,
            output_tests_dependencies=None,
            json=False,
            url=False,
        )
        self.patcher1 = patch("ledgered.manifest.cli.print", PrintMock())
        self.patcher2 = patch("ledgered.manifest.cli.set_parser")
        self.print_mock = self.patcher1.start()
        self.parser_mock = self.patcher2.start()
        self.parser_mock().parse_args = lambda: self.args

    def tearDown(self):
        self.patcher1.stop()
        self.patcher2.stop()

    @property
    def text(self):
        return self.print_mock.get()

    @property
    def json(self):
        return loads(self.print_mock.get())

    def test_use_cases_and_dependencies_text(self):
        self.args.output_use_cases = list()
        self.args.output_tests_dependencies = list()
        self.assertIsNone(main())
        # the output needs to be cut in chunks, as the lists can be re-ordered
        # during the parsing of the manifest
        text = self.text
        for chunk in UC_D_EXPECTED_TEXT_CHUNKS:
            self.assertIn(chunk, text)

    def test_cases_and_dependencies_json(self):
        self.args.output_use_cases = list()
        self.args.output_tests_dependencies = list()
        self.args.json = True
        self.assertIsNone(main())
        # like before, the output needs to be divided and the lists compared
        # separately as they may have been re-ordered
        json = self.json
        dependencies = json["tests"]["dependencies"].pop("testing_develop")
        self.assertDictEqual(json, UC_D_EXPECTED_JSON)
        self.assertCountEqual(dependencies, EXPECTED_DEPENDENCIES_JSON)

    def test_single_field(self):
        self.args.output_sdk = True
        self.assertIsNone(main())
        self.assertEqual(self.text, "c")

        self.args.json = True
        self.assertIsNone(main())
        self.assertEqual(self.json, {"sdk": "c"})

    def test_full_text(self):
        self.args.output_sdk = True
        self.args.output_devices = True
        self.args.output_build_directory = True
        self.args.output_tests_unit_directory = True
        self.args.output_tests_pytest_directory = True
        self.args.output_use_cases = list()
        self.assertIsNone(main())
        self.assertEqual(FULL_EXPECTED_TEXT, self.text)

    def test_full_json(self):
        self.args.output_sdk = True
        self.args.output_devices = True
        self.args.output_build_directory = True
        self.args.output_tests_unit_directory = True
        self.args.output_tests_pytest_directory = True
        self.args.output_use_cases = list()
        self.args.json = True
        self.assertIsNone(main())
        self.assertEqual(FULL_EXPECTED_JSON, self.json)

    def test_single_leaf(self):
        self.args.source = TEST_MANIFEST_DIRECTORY / "one_leaf.toml"
        self.args.output_tests_dependencies = list()
        expected_text = """testing_develop:
 0.
  url: https://github.com/<owner>/<app-repository>
  ref: develop
  use_case: debug
  application_directory: some/dir/.dependencies/<app-repository>-develop-debug"""
        expected_json = {
            "testing_develop": [
                {
                    "url": "https://github.com/<owner>/<app-repository>",
                    "ref": "develop",
                    "use_case": "debug",
                    "application_directory": "some/dir/.dependencies/<app-repository>-develop-debug",
                }
            ]
        }
        self.assertIsNone(main())
        self.assertEqual(self.text, expected_text)

        self.args.json = True
        self.assertIsNone(main())
        self.assertEqual(self.json, expected_json)

    def test_error_inexisting_use_cases(self):
        self.args.output_use_cases = ["does not exist"]
        with self.assertRaises(SystemExit):
            main()

    def test_error_inexisting_tests_dependencies(self):
        self.args.output_tests_dependencies = ["does not exist"]
        with self.assertRaises(SystemExit):
            main()

    def test_error_inexisting_tests_unit_directory(self):
        self.args.source = TEST_MANIFEST_DIRECTORY / "minimal.toml"
        # non existing unit directory
        self.args.output_tests_unit_directory = True
        with self.assertRaises(SystemExit):
            main()

    def test_error_inexisting_tests_pytest_directory(self):
        self.args.source = TEST_MANIFEST_DIRECTORY / "minimal.toml"
        # non existing unit directory
        self.args.output_tests_pytest_directory = True
        with self.assertRaises(SystemExit):
            main()

    def test_loading_from_url(self):
        self.args.source = "app-boilerplate"
        self.args.url = True
        self.assertIsNone(main())


class TestCLIset_parser(TestCase):
    diffMax = None

    def test_set_parser(self):
        parser = set_parser()
        # a bit of a blank test really. But that improves the coverage DAMMIT
        self.assertIsInstance(parser, ArgumentParser)
