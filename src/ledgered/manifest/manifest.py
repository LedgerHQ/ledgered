import logging
import toml
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, IO, Optional, Union

from .app import AppConfig
from .constants import MANIFEST_FILE_NAME
from .tests import TestsConfig
from .use_cases import UseCasesConfig


class RepoManifest(ABC):

    @abstractmethod
    def check(self, directory: Union[str, Path]) -> None:
        raise NotImplementedError

    @staticmethod
    def __from_file(filee: Union[Path, IO]) -> "RepoManifest":
        manifest = toml.load(filee)
        cls: type
        if "rust-app" in manifest:
            cls = LegacyManifest
        else:
            cls = Manifest
        return cls(**manifest)

    @classmethod
    def from_io(cls, manifest_io: IO) -> "RepoManifest":
        return cls.__from_file(manifest_io)

    @classmethod
    def from_path(cls, path: Path) -> "RepoManifest":
        if path.is_dir():
            path = path / MANIFEST_FILE_NAME
        assert path.is_file(), f"'{path.resolve()}' is not a manifest file."
        return cls.__from_file(path)


@dataclass
class Manifest(RepoManifest):
    app: AppConfig
    tests: Optional[TestsConfig]
    use_cases: Optional[UseCasesConfig]

    def __init__(self, app: Dict,
                 tests: Optional[Dict] = None,
                 use_cases: Optional[Dict] = None) -> None:
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
        build_file = base_directory / self.app.build_directory / \
            ("Cargo.toml" if self.app.is_rust else "Makefile")
        logging.info("Checking existence of file %s", build_file)
        assert build_file.is_file(), f"No file '{build_file}' (from the given base directory " \
            f"'{base_directory}' + the manifest path '{self.app.build_directory}') was found"


class LegacyManifest(RepoManifest):

    def __init__(self, **kwargs) -> None:
        try:
            self.manifest_path = Path(kwargs["rust-app"]["manifest-path"])
        except KeyError as e:
            msg = "Given manifest is not a legacy manifest (does not contain 'rust-app' section)"
            logging.error(msg)
            raise ValueError(msg) from e

    def check(self, base_directory: Union[str, Path]) -> None:
        base_directory = Path(base_directory)
        assert base_directory.is_dir(), f"Given '{base_directory}' must be an existing directory"
        cargo_toml = base_directory / self.manifest_path
        logging.info("Checking existence of file %s", cargo_toml)
        assert cargo_toml.is_file(), f"No file '{cargo_toml}' (from the given base directory " \
            f"'{base_directory}' + the manifest path '{self.manifest_path}') was found"

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "LegacyManifest":
        path = Path(path)
        if path.is_dir():
            path = path / MANIFEST_FILE_NAME
        assert path.is_file(), f"'{path.resolve()}' is not a manifest file."
        return cls(**toml.load(path))
