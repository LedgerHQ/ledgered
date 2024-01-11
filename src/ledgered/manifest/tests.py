from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union


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
