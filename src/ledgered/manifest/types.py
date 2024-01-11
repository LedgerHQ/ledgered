from typing import Dict, List, Union


class Jsonable:

    @property
    def json(self) -> Union[Dict, List]:
        output = dict()
        for key, value in self.__dict__.items():
            if isinstance(value, Jsonable):
                output[key] = value.json
            else:
                output[key] = str(value)
        return output


class JsonList(list, Jsonable):

    @property
    def json(self) -> List:
        output = list()
        for element in self:
            if isinstance(element, Jsonable):
                output.append(element.json)
            else:
                output.append(str(element))
        return output


class JsonSet(set, Jsonable):

    @property
    def json(self) -> List:
        output = list()
        for element in self:
            if isinstance(element, Jsonable):
                output.append(element.json)
            else:
                output.append(str(element))
        return output


class JsonDict(dict, Jsonable):

    @property
    def json(self) -> Dict:
        output = dict()
        for key, value in self.items():
            if isinstance(value, Jsonable):
                output[key] = value.json
            else:
                output[key] = str(value)
        return output
