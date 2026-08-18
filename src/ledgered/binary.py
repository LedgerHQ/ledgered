import logging
from argparse import ArgumentParser
from dataclasses import asdict, dataclass
from pathlib import Path

from elftools.elf.elffile import ELFFile

from ledgered.serializers import Jsonable

LEDGER_PREFIX = "ledger."
DEFAULT_GRAPHICS = "bagl"


@dataclass
class Sections(Jsonable):
    api_level: str | None = None
    app_name: str | None = None
    app_version: str | None = None
    rust_sdk_name: str | None = None
    rust_sdk_version: str | None = None
    sdk_graphics: str = DEFAULT_GRAPHICS
    sdk_hash: str | None = None
    sdk_name: str | None = None
    sdk_version: str | None = None
    target: str | None = None
    target_id: str | None = None
    target_name: str | None = None
    target_version: str | None = None
    app_flags: str | None = None

    def __str__(self) -> str:
        return "\n".join(f"{key} {value}" for key, value in sorted(asdict(self).items()))


class LedgerBinaryApp:
    def __init__(self, binary_path: str | Path):
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

    @property
    def sections(self) -> Sections:
        return self._sections


def set_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="ledger-binary",
        description="Utilitary to parse Ledger embedded application ELF file and output metadatas",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("binary", type=Path, help="The ledger embedded application ELF file")
    parser.add_argument("-j", "--json", required=False, action="store_true", help="outputs as JSON rather than text")
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
