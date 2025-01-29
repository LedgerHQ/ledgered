from dataclasses import dataclass
from unittest import TestCase

from ledgered.serializers import Jsonable, JsonList, JsonSet, JsonDict


@dataclass
class JsonableTest1(Jsonable):
    base: str

    def __hash__(self):
        return 1


@dataclass
class JsonableTest2(Jsonable):
    one: str
    two: JsonableTest1


class TestTypesModule(TestCase):
    def setUp(self):
        self.jt1 = JsonableTest1("base")

    def test_Jsonable_json(self):
        instance = JsonableTest2("one", self.jt1)
        expected = {"one": "one", "two": {"base": "base"}}
        self.assertEqual(instance.json, expected)

    def test_JsonList_json(self):
        integer = 4
        string = "str"
        j_list = JsonList()
        j_list.append(integer)
        j_list.append(string)
        j_list.append(self.jt1)
        expected = [integer, string, {"base": "base"}]
        self.assertEqual(j_list.json, expected)

    def test_JsonSet_json(self):
        integer = 4
        string = "str"
        j_set = JsonSet()
        j_set.add(integer)
        j_set.add(string)
        j_set.add(self.jt1)
        expected = [integer, string, {"base": "base"}]
        result = j_set.json
        # the JsonSet.json returns a list, but the set may have broken the order so we can't
        # directly compare the two lists.
        self.assertIsInstance(result, list)
        self.assertCountEqual(result, expected)

    def test_JsonDict_json(self):
        j_dict = JsonDict()
        j_dict[4] = 5
        j_dict["base"] = self.jt1
        expected = {4: 5, "base": {"base": "base"}}
        self.assertEqual(j_dict.json, expected)
