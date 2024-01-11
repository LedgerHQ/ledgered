import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from .constants import MANIFEST_FILE_NAME
from .manifest import Manifest, LegacyManifest
from .utils import getLogger


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
    logger = getLogger()
    args = parse_args()
    assert args.manifest.is_file(), f"'{args.manifest.resolve()}' does not appear to be a file."
    manifest = args.manifest.resolve()

    # verbosity
    if args.verbose == 1:
        logger.setLevel(logging.INFO)
    elif args.verbose > 1:
        logger.setLevel(logging.DEBUG)

    # compatibility check: legacy manifest cannot display sdk, devices, unit/pytest directory
    if args.legacy and (args.output_sdk or args.output_devices or args.output_devices
                        or args.output_unit_directory or args.output_pytest_directory):
        raise ValueError("'-l' option is not compatible with '-os', '-od', 'ou' or 'op'")

    # parsing the manifest
    if args.legacy:
        logger.info("Expecting a legacy manifest")
        manifest_cls = LegacyManifest
    else:
        logger.info("Expecting a classic manifest")
        manifest_cls = Manifest
    repo_manifest = manifest_cls.from_path(manifest)

    # check directory path against manifest data
    if args.check is not None:
        logger.info("Checking the manifest")
        repo_manifest.check(args.check)
        return

    # no check
    logger.info("Displaying manifest info")
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
            logger.error("This manifest does not contains the 'tests.unit_directory' field")
            sys.exit(2)
        display_content["unit_directory"] = repo_manifest.tests.unit_directory
    if args.output_pytest_directory:
        if repo_manifest.tests is None or repo_manifest.tests.pytest_directory is None:
            logger.error("This manifest does not contains the 'tests.pytest_directory' field")
            sys.exit(2)
        display_content["pytest_directory"] = repo_manifest.tests.pytest_directory

    # only one line to display, or several
    if len(display_content) == 1:
        print(display_content.popitem()[1])
    else:
        for key, value in display_content.items():
            print(f"{key}: {value}")
