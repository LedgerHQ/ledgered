import logging
import toml
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, IO, Optional, Union

from ledgered.serializers import Jsonable
from .app import AppConfig
from .constants import MANIFEST_FILE_NAME
from .tests import TestsConfig
from .use_cases import UseCasesConfig


@dataclass
class Manifest(Jsonable):
    app: AppConfig
    tests: Optional[TestsConfig]
    use_cases: Optional[UseCasesConfig]

    def __init__(
        self, app: Dict, tests: Optional[Dict] = None, use_cases: Optional[Dict] = None
    ) -> None:
        self.app = AppConfig(**app)
        self.tests = None if tests is None else TestsConfig(**tests)
        self.use_cases = None if use_cases is None else UseCasesConfig(**use_cases)

    @classmethod
    def from_string(cls, content: str) -> "Manifest":
        return cls(**toml.loads(content))

    @classmethod
    def from_io(cls, manifest_io: IO) -> "Manifest":
        return cls(**toml.load(manifest_io))

    @classmethod
    def from_path(cls, path: Path) -> "Manifest":
        if path.is_dir():
            path = path / MANIFEST_FILE_NAME
        assert path.is_file(), f"'{path.resolve()}' is not a manifest file."
        return cls(**toml.load(path))

    def check(self, base_directory: Union[str, Path]) -> None:
        base_directory = Path(base_directory)
        assert base_directory.is_dir(), f"Given '{base_directory}' must be a directory"
        build_file = (
            base_directory
            / self.app.build_directory
            / ("Cargo.toml" if self.app.is_rust else "Makefile")
        )
        logging.info("Checking existence of file %s", build_file)
        assert build_file.is_file(), (
            f"No file '{build_file}' (from the given base directory "
            f"'{base_directory}' + the manifest path '{self.app.build_directory}') was found"
        )
