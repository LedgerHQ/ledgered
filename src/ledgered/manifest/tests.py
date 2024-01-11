from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union

from .utils import getLogger
from .types import Jsonable, JsonDict, JsonSet


class DuplicateDependency(ValueError):
    pass


@dataclass
class TestDependencyConfig(Jsonable):
    url: str
    ref: str
    use_case: Optional[str]

    def __init__(self, url: str, ref: str, use_case: Optional[str] = None) -> None:
        self.url = url
        self.ref = ref
        self.use_case = use_case or "default"

    @property
    def dir(self):
        return f"{self.url}-{self.ref}-{self.use_case}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(object, TestDependencyConfig):
            return False
        return self.dir == other.dir

    def __hash__(self) -> int:
        return int.from_bytes(self.dir.encode(), "big")


@dataclass
class TestDependenciesConfig(Jsonable):
    dependencies: JsonSet

    def __init__(self, dependencies: List[Dict]) -> None:
        logger = getLogger()
        self.dependencies = JsonSet()
        for dep in dependencies:
            dependency = TestDependencyConfig(**dep)
            if dependency in self.dependencies:
                logger.error("Dependency duplication!")
                raise DuplicateDependency(dependency)
            self.dependencies.add(dependency)
            logger.debug("Dependency %s added", dependency)

    @property
    def json(self):
        return self.dependencies.json


@dataclass
class TestsConfig(Jsonable):
    __test__ = False  # deactivate pytest discovery warning

    unit_directory: Optional[Path]
    pytest_directory: Optional[Path]
    dependencies: Optional[JsonDict]

    def __init__(self,
                 unit_directory: Optional[Union[str, Path]] = None,
                 pytest_directory: Optional[Union[str, Path]] = None,
                 dependencies: Optional[Dict[str, List]] = None) -> None:
        logger = getLogger()
        logger.debug("Parsing test dependencies")
        self.unit_directory = None if unit_directory is None else Path(unit_directory)
        self.pytest_directory = None if pytest_directory is None else Path(pytest_directory)
        if dependencies is None:
            self.dependencies = None
        else:
            self.dependencies = JsonDict()
            for key, value in dependencies.items():
                logger.info("Parsing dependencies for '%s' tests", key)
                self.dependencies[key] = TestDependenciesConfig(value)
