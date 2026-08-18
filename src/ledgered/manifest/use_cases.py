from dataclasses import dataclass

from ledgered.serializers import Jsonable, JsonDict

from .constants import DEFAULT_USE_CASE


@dataclass
class UseCasesConfig(Jsonable):
    cases: JsonDict

    def __init__(self, **cases: dict | None) -> None:
        for key, value in cases.items():
            if not isinstance(value, str):
                raise ValueError(f"Use case '{key} = {value}' should have '{value}' as a string, not a {type(value)}")
            if key == DEFAULT_USE_CASE:
                raise ValueError(f"'{key}' use case is reserved and cannot be overridden")
        self.cases = JsonDict(cases)

    def get(self, name: str) -> str:
        if name == DEFAULT_USE_CASE:
            return ""
        return self.cases[name]

    @property
    def json(self) -> dict:
        return self.cases.json
