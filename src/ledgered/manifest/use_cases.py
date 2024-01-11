from dataclasses import dataclass
from typing import Dict, Optional

from .types import Jsonable, JsonDict

RESERVED = "default"


@dataclass
class UseCasesConfig(Jsonable):
    cases: JsonDict

    def __init__(self, **cases: Optional[Dict]) -> None:
        if cases is None:
            self.cases = JsonDict()
            return
        for key, value in cases.items():
            if not isinstance(value, str):
                raise ValueError(f"Use case '{key} = {value}' should have '{value}' as a string, "
                                 f"not a {type(value)}")
            if key == RESERVED:
                raise ValueError(f"'{key}' use case is reserved and cannot be overridden")
        self.cases = JsonDict(cases)

    def get(self, name: str) -> str:
        if name == RESERVED:
            return str()
        return self.cases[name]

    @property
    def json(self) -> Dict:
        return self.cases.json
