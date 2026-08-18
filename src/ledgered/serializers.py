from typing import Any


def to_str_int(value: Any) -> int | str:
    return str(value) if not isinstance(value, int) else value


class Jsonable:
    @property
    def json(self) -> dict | list:
        output: dict[str | int, Any] = dict()
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                # 'hidden' properties are not to be included into the output
                continue
            if isinstance(value, Jsonable):
                output[key] = value.json
            else:
                output[key] = to_str_int(value)
        return output


class JsonList(list, Jsonable):
    @property
    def json(self) -> list:
        output: list[Any] = list()
        for element in self:
            if isinstance(element, Jsonable):
                output.append(element.json)
            else:
                output.append(to_str_int(element))
        return output


class JsonSet(set, Jsonable):
    @property
    def json(self) -> list:
        output: list[Any] = list()
        for element in self:
            if isinstance(element, Jsonable):
                output.append(element.json)
            else:
                output.append(to_str_int(element))
        return output


class JsonDict(dict, Jsonable):
    @property
    def json(self) -> dict:
        output: dict[str | int, Any] = dict()
        for key, value in self.items():
            if isinstance(value, Jsonable):
                output[key] = value.json
            else:
                output[key] = to_str_int(value)
        return output
