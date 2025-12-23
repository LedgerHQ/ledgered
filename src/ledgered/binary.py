import json
import logging
from argparse import ArgumentParser
from dataclasses import asdict, dataclass
from elftools.elf.elffile import ELFFile
from pathlib import Path
from typing import Optional, Union

from ledgered.devices import Devices
from ledgered.serializers import Jsonable

LEDGER_PREFIX = "ledger."
DEFAULT_GRAPHICS = "bagl"


@dataclass
class Sections(Jsonable):
    api_level: Optional[str] = None
    app_name: Optional[str] = None
    app_version: Optional[str] = None
    rust_sdk_name: Optional[str] = None
    rust_sdk_version: Optional[str] = None
    sdk_graphics: str = DEFAULT_GRAPHICS
    sdk_hash: Optional[str] = None
    sdk_name: Optional[str] = None
    sdk_version: Optional[str] = None
    target: Optional[str] = None
    target_id: Optional[str] = None
    target_name: Optional[str] = None
    target_version: Optional[str] = None
    app_flags: Optional[str] = None

    def __str__(self) -> str:
        return "\n".join(f"{key} {value}" for key, value in sorted(asdict(self).items()))


class LedgerBinaryApp:
    def __init__(self, binary_path: Union[str, Path]):
        if isinstance(binary_path, str):
            binary_path = Path(binary_path)
        self._path = binary_path = binary_path.resolve()
        logging.info("Parsing binary '%s'", self._path)
        with self._path.open("rb") as filee:
            sections = {
                s.name.replace(LEDGER_PREFIX, ""): s.data().decode().strip()
                for s in ELFFile(filee).iter_sections()
                if LEDGER_PREFIX in s.name
            }
        self._sections = Sections(**sections)

        # Rust apps store app_name/app_version/app_flags in companion JSON file
        if self.is_rust_app:
            self._load_metadata_from_json()

    def _load_metadata_from_json(self) -> None:
        """Load app metadata from companion app_<target>.json file.

        Rust applications don't embed app_name, app_version, and app_flags in the ELF.
        Instead, these are stored in a JSON file named app_<target>.json in the same directory.
        This method is called only for Rust applications.

        Note: The target name in the ELF may differ from the JSON filename.
        For example, nanos2 -> nanosplus, nanos+ -> nanosplus.
        """
        target = self._sections.target
        if not target:
            logging.warning(
                "Rust app detected but no target found, cannot locate companion JSON file"
            )
            return

        # Try multiple naming patterns to find the JSON file
        json_path = self._find_json_file(target)
        if not json_path:
            logging.warning(
                "Rust app detected but companion JSON file not found for target '%s' in %s",
                target,
                self._path.parent,
            )
            return

        try:
            logging.info("Loading Rust app metadata from %s", json_path)
            with json_path.open("r") as f:
                data = json.load(f)

            if "name" in data:
                self._sections.app_name = data["name"]
                logging.debug("Loaded app_name: %s", self._sections.app_name)

            if "version" in data:
                self._sections.app_version = data["version"]
                logging.debug("Loaded app_version: %s", self._sections.app_version)

            if "flags" in data:
                self._sections.app_flags = data["flags"]
                logging.debug("Loaded app_flags: %s", self._sections.app_flags)

        except (json.JSONDecodeError, OSError) as e:
            logging.error("Failed to load companion JSON file %s: %s", json_path, e)

    def _find_json_file(self, target: str) -> Optional[Path]:
        """Find the companion JSON file using multiple naming patterns.

        Tries different naming conventions:
        1. Exact target name (e.g., nanos2 -> app_nanos2.json)
        2. Canonical device name (e.g., nanos2 -> app_nanosp.json)
        3. All device aliases (e.g., nanos+, nanosplus for NanoS+)

        Args:
            target: The target name from the ELF binary

        Returns:
            Path to the JSON file if found, None otherwise
        """
        candidates = [target]  # Start with exact target name

        try:
            device = Devices.get_by_name(target)
            # Add canonical device name
            candidates.append(device.name)
            # Add all known aliases
            candidates.extend(device.names)
        except KeyError:
            logging.debug("Unknown device '%s', trying exact name only", target)

        # Try all candidates
        for candidate in candidates:
            json_path = self._path.parent / f"app_{candidate}.json"
            if json_path.exists():
                logging.debug("Found JSON file with pattern '%s': %s", candidate, json_path)
                return json_path

        return None

    def _normalize_target_name(self, target: str) -> str:
        """Normalize target name to match JSON filename conventions.

        Device names can vary (e.g., nanos2, nanos+, nanosplus all refer to the same device).
        The JSON files use a canonical naming (nanosplus, flex, stax, etc.).

        Args:
            target: The target name from the ELF binary

        Returns:
            The normalized target name for JSON file lookup
        """
        try:
            device = Devices.get_by_name(target)
            return device.name
        except KeyError:
            # If device is unknown, return the original target name
            logging.debug("Unknown device '%s', using target name as-is", target)
            return target

    @property
    def sections(self) -> Sections:
        return self._sections

    @property
    def is_rust_app(self) -> bool:
        """Returns True if this is a Rust application."""
        return (
            self._sections.rust_sdk_name is not None or self._sections.rust_sdk_version is not None
        )


def set_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="ledger-binary",
        description="Utilitary to parse Ledger embedded application ELF file and output metadatas",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("binary", type=Path, help="The ledger embedded application ELF file")
    parser.add_argument(
        "-j", "--json", required=False, action="store_true", help="outputs as JSON rather than text"
    )
    return parser


def main() -> None:
    args = set_parser().parse_args()
    assert args.binary.is_file(), f"'{args.binary.resolve()}' does not appear to be a file."

    # verbosity
    if args.verbose == 1:
        logging.root.setLevel(logging.INFO)
    elif args.verbose > 1:
        logging.root.setLevel(logging.DEBUG)

    app = LedgerBinaryApp(args.binary)
    if args.json:
        print(app.sections.json)
    else:
        print(app.sections)
