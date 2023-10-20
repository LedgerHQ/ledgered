import logging
import sys
import toml
from abc import ABC, abstractmethod
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


class RepoManifest(ABC):

    @abstractmethod
    def check(self, directory: Union[str, Path]) -> None:
        raise NotImplementedError


@dataclass
class Manifest(RepoManifest):
    app: AppConfig
    tests: Optional[TestsConfig]

    def __init__(self, app: Dict, tests: Optional[Dict] = None) -> None:
        self.app = AppConfig(**app)
        self.tests = None if tests is None else TestsConfig(**tests)

    @staticmethod
    def from_string(content: str) -> "Manifest":
        return Manifest(**toml.loads(content))

    @staticmethod
    def from_io(manifest_io: IO) -> "Manifest":
        return Manifest(**toml.load(manifest_io))

    @staticmethod
    def from_path(path: Path) -> "Manifest":
        if path.is_dir():
            path = path / MANIFEST_FILE_NAME
        assert path.is_file(), f"'{path.resolve()}' is not a manifest file."
        return Manifest(**toml.load(path))

    def check(self, base_directory: Union[str, Path]) -> None:
        base_directory = Path(base_directory)
        assert base_directory.is_dir(), f"Given '{base_directory}' must be a directory"
        build_file = base_directory / self.app.build_directory / \
            ("Cargo.toml" if self.app.is_rust else "Makefile")
        logging.info("Checking existence of file %s", build_file)
        assert build_file.is_file(), f"No file '{build_file}' (from the given base directory " \
            f"'{base_directory}' + the manifest path '{self.app.build_directory}') was found"


class LegacyManifest(RepoManifest):

    def __init__(self, manifest_path: Union[str, Path]) -> None:
        manifest_path = Path(manifest_path)
        if manifest_path.is_dir():
            manifest_path = manifest_path / MANIFEST_FILE_NAME
        data = toml.load(str(manifest_path))
        self.manifest_path = Path(data["rust-app"]["manifest-path"])

    def check(self, base_directory: Union[str, Path]) -> None:
        base_directory = Path(base_directory)
        assert base_directory.is_dir(), f"Given '{base_directory}' must be an existing directory"
        cargo_toml = base_directory / self.manifest_path
        logging.info("Checking existence of file %s", cargo_toml)
        assert cargo_toml.is_file(), f"No file '{cargo_toml}' (from the given base directory " \
            f"'{base_directory}' + the manifest path '{self.manifest_path}') was found"


# CLI-oriented code #


def parse_args() -> Namespace:  # pragma: no cover
    parser = ArgumentParser(prog="ledger-manifest",
                            description="Utilitary to parse and check an application "
                            "'ledger_app.toml' manifest")

    # generic options
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument("-l",
                        "--legacy",
                        required=False,
                        action="store_true",
                        default=False,
                        help="Specifies if the 'ledger_app.toml' file is a legacy one (with "
                        "'rust-app' section)")
    parser.add_argument("-c",
                        "--check",
                        required=False,
                        type=Path,
                        default=None,
                        help="Check the manifest content against the provided directory.")

    # display options
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

    # verbosity
    if args.verbose == 1:
        logging.root.setLevel(logging.INFO)
    elif args.verbose > 1:
        logging.root.setLevel(logging.DEBUG)

    # compatibility check: legacy manifest cannot display sdk, devices, unit/pytest directory
    if args.legacy and (args.output_sdk or args.output_devices or args.output_devices
                        or args.output_unit_directory or args.output_pytest_directory):
        raise ValueError("'-l' option is not compatible with '-os', '-od', 'ou' or 'op'")

    # parsing the manifest
    if args.legacy:
        logging.info("Expecting a legacy manifest")
        repo_manifest = LegacyManifest(manifest)
    else:
        logging.info("Expecting a classic manifest")
        repo_manifest = Manifest.from_path(manifest)

    # check directory path against manifest data
    if args.check is not None:
        logging.info("Checking the manifest")
        repo_manifest.check(args.check)
        return

    # no check
    logging.info("Displaying manifest info")
    display_content = dict()

    # build_directory can be 'deduced' from legacy manifest
    if args.output_build_directory:
        if args.legacy:
            display_content["build_directory"] = repo_manifest.manifest_path.parent
        else:
            display_content["build_directory"] = repo_manifest.app.build_directory

    # unlike build_directory, other field can not be deduced from legacy manifest
    if args.output_sdk:
        display_content["sdk"] = repo_manifest.app.sdk
    if args.output_devices:
        display_content["devices"] = list(repo_manifest.app.devices)
    if args.output_unit_directory:
        if repo_manifest.tests is None or repo_manifest.tests.unit_directory is None:
            logging.error("This manifest does not contains the 'tests.unit_directory' field")
            sys.exit(2)
        display_content["unit_directory"] = repo_manifest.tests.unit_directory
    if args.output_pytest_directory:
        if repo_manifest.tests is None or repo_manifest.tests.pytest_directory is None:
            logging.error("This manifest does not contains the 'tests.pytest_directory' field")
            sys.exit(2)
        display_content["pytest_directory"] = repo_manifest.tests.pytest_directory

    # only one line to display, or several
    if len(display_content) == 1:
        print(display_content.popitem()[1])
    else:
        for key, value in display_content.items():
            print(f"{key}: {value}")
