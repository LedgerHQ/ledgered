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
        l = JsonList()
        l.append(integer)
        l.append(string)
        l.append(self.jt1)
        expected = [integer, string, {"base": "base"}]
        self.assertEqual(l.json, expected)

    def test_JsonSet_json(self):
        integer = 4
        string = "str"
        l = JsonSet()
        l.add(integer)
        l.add(string)
        l.add(self.jt1)
        expected = [integer, string, {"base": "base"}]
        result = l.json
        # the JsonSet.json returns a list, but the set may have broken the order so we can't
        # directly compare the two lists.
        self.assertIsInstance(result, list)
        self.assertCountEqual(result, expected)

    def test_JsonDict_json(self):
        l = JsonDict()
        l[4] = 5
        l["base"] = self.jt1
        expected = {4: 5, "base": {"base": "base"}}
        self.assertEqual(l.json, expected)
