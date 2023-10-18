import logging
import sys
import toml
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, IO, Iterable, Optional, Set, Union

MANIFEST_FILE_NAME = "ledger_app.toml"
EXISTING_DEVICES = ["nanos", "nanox", "nanos+", "stax"]


@dataclass
class TestsConfig:
    __test__ = False  # deactivate pytest discovery warning

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
    devices: Set[str]

    def __init__(self, sdk: str, build_directory: Union[str, Path], devices: Iterable[str]) -> None:
        sdk = sdk.lower()
        if sdk not in ["rust", "c"]:
            raise ValueError(f"'{sdk}' unknown. Must be either 'C' or 'Rust'")
        self.sdk = sdk
        self.build_directory = Path(build_directory)
        devices = {device.lower() for device in devices}
        unknown_devices = devices.difference(EXISTING_DEVICES)
        if unknown_devices:
            unknown_devices_str = "', '".join(unknown_devices)
            raise ValueError(f"Unknown devices: '{unknown_devices_str}'")
        self.devices = devices

    @property
    def is_rust(self) -> bool:
        return self.sdk == "rust"

    @property
    def is_c(self) -> bool:
        return not self.is_rust


@dataclass
class RepoManifest:
    app: AppConfig
    tests: Optional[TestsConfig]

    def __init__(self, app: Dict, tests: Optional[Dict] = None) -> None:
        self.app = AppConfig(**app)
        self.tests = None if tests is None else TestsConfig(**tests)

    @staticmethod
    def from_string(content: str) -> "RepoManifest":
        return RepoManifest(**toml.loads(content))

    @staticmethod
    def from_io(manifest_io: IO) -> "RepoManifest":
        return RepoManifest(**toml.load(manifest_io))

    @staticmethod
    def from_path(path: Path) -> "RepoManifest":
        if path.is_dir():
            path = path / MANIFEST_FILE_NAME
        assert path.is_file(), f"'{path.resolve()}' is not a manifest file."
        with path.open() as manifest_io:
            return RepoManifest.from_io(manifest_io)


# CLI-oriented code #


def parse_args() -> Namespace:  # pragma: no cover
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


def main():  # pragma: no cover
    args = parse_args()
    assert args.manifest.is_file(), f"'{args.manifest.resolve()}' does not appear to be a file."
    manifest = args.manifest.resolve()
    repo_manifest = RepoManifest.from_path(manifest)

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
