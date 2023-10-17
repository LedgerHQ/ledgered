import logging
import sys
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from toml import loads

MANIFEST_FILE_NAME = "ledger_app.toml"


@dataclass
class TestsConfig:
    unit_directory: Optional[Path]
    pytest_directory: Optional[Path]

    def __init__(self,
                 unit_directory: Optional[Union[str, Path]] = None,
                 pytest_directory: Optional[Union[str, Path]] = None) -> None:
        self.unit_directory = None if unit_directory is None else Path(unit_directory)
        self.pytest_directory = None if pytest_directory is None else Path(pytest_directory)


@dataclass
class AppConfig:
    sdk: str
    build_directory: Path
    devices: List[str]

    def __init__(self, sdk: str, build_directory: Union[str, Path], devices: List[str]) -> None:
        if not sdk.lower() in ["rust", "c"]:
            raise ValueError(f"'{sdk}' unknown. Must be either 'C' or 'Rust'")
        self.sdk = sdk.lower()
        self.build_directory = Path(build_directory)
        self.devices = devices

    @property
    def is_rust(self) -> bool:
        return self.sdk == "rust"

    @property
    def is_c(self) -> bool:
        return True


@dataclass
class RepoManifest:
    app: AppConfig
    tests: Optional[TestsConfig]

    def __init__(self, app: Dict, tests: Optional[Dict] = None) -> None:
        self.app = AppConfig(**app)
        self.tests = None if tests is None else TestsConfig(**tests)


def parse_manifest(content: str, root: Path = Path(".")) -> RepoManifest:
    """
    Parse the raw content of an application manifest ('ledger_app.toml') and
    extract relevant information.
    Returned value will depends on if the application is a C or a Rust one.
    """
    return RepoManifest(**loads(content))


# CLI-oriented code #


def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("manifest",
                        type=Path,
                        help=f"The manifest file, generally '{MANIFEST_FILE_NAME}' at the root of "
                        "the application's repository")
    parser.add_argument("-os",
                        "--output-sdk",
                        required=False,
                        action='store_true',
                        default=False,
                        help="outputs the SDK type")
    parser.add_argument("-ob",
                        "--output-build-directory",
                        required=False,
                        action='store_true',
                        default=False,
                        help="outputs the build directory (where the Makefile in C app, or the "
                        "Cargo.toml in Rust app is expected to be)")
    parser.add_argument("-od",
                        "--output-devices",
                        required=False,
                        action='store_true',
                        default=False,
                        help="outputs the list of devices supported by the application")
    # 'app' section
    # 'tests' section
    parser.add_argument("-ou",
                        "--output-unit-directory",
                        required=False,
                        action='store_true',
                        default=False,
                        help="outputs the directory of the unit tests. Fails if none")
    parser.add_argument("-op",
                        "--output-pytest-directory",
                        required=False,
                        action='store_true',
                        default=False,
                        help="outputs the directory of the pytest (functional) tests. Fails if "
                        "none")
    return parser.parse_args()


def main():
    args = parse_args()
    assert args.manifest.is_file(), f"'{args.manifest.resolve()}' does not appear to be a file."
    manifest = args.manifest.resolve()
    with manifest.open() as filee:
        repo_manifest = parse_manifest(filee.read())

    display_content = dict()
    if args.output_sdk:
        display_content["sdk"] = repo_manifest.app.sdk
    if args.output_build_directory:
        display_content["build_directory"] = repo_manifest.app.build_directory
    if args.output_devices:
        display_content["devices"] = repo_manifest.app.devices
    if args.output_unit_directory:
        if repo_manifest.tests is None or repo_manifest.test.unit_directory is None:
            logging.error("This manifest does not contains the 'tests.unit_directory' field")
            sys.exit(2)
        display_content["unit_directory"] = repo_manifest.tests.unit_directory
    if args.output_pytest_directory:
        if repo_manifest.tests is None or repo_manifest.test.pytest_directory is None:
            logging.error("This manifest does not contains the 'tests.pytest_directory' field")
            sys.exit(2)
        display_content["pytest_directory"] = repo_manifest.test.pytest_directory

    # only one line to display, or several
    if len(display_content) == 1:
        print(display_content.popitem()[1])
    else:
        for key, value in display_content.items():
            print(f"{key}: {value}")
