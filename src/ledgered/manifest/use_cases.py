from dataclasses import dataclass
from typing import Dict, Optional

RESERVED = "default"


@dataclass
class UseCasesConfig:
    cases: Dict[str, str]

    def __init__(self, **cases: Optional[Dict]) -> None:
        if cases is None:
            self.cases = {}
            return
        for key, value in cases.items():
            if not isinstance(value, str):
                raise ValueError(f"Use case '{key} = {value}' should have '{value}' as a string, "
                                 f"not a {type(value)}")
            if key == RESERVED:
                raise ValueError(f"'{key}' use case is reserved and cannot be overriden")
        self.cases = cases

    def get(self, name: str) -> str:
        if name == RESERVED:
            return str()
        self.cases[name]
