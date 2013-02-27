import unittest

import drot


class DrotTestCase(unittest.TestCase):

    @drot.definition
    class SheldonBeatsDoctor(object):
        def __init__(self, array=None, dictionary=None, member=None,
                     a=None, b=None):
            self.array = array or []
            self.dictionary = dictionary or {}
            self.member = member
            self.a = a or "TARDIS"
            self.b = b or "DOCTOR"

        @classmethod
        @drot.parser('a')
        def __parse_a(cls, value):
            return "sheldon"

        @drot.formatter('b')
        def __format_b(self, value):
            return "bazzinga!"

    def test_no_values_are_set(self):
        testee = self.SheldonBeatsDoctor()
        self.assertEquals({}, testee.to_dict())

    def test_some_values_are_set(self):
        testee = self.SheldonBeatsDoctor(member="foo")
        self.assertEquals({'member': 'foo'}, testee.to_dict())

    def test_array_is_set(self):
        testee = self.SheldonBeatsDoctor(member="bar", array=[1, 2, 3, 4])
        self.assertEquals({'member': 'bar', 'array': [1, 2, 3, 4]},
                          testee.to_dict())

    def test_dictionary_is_set(self):
        cool_dict = {"name": "instance-000ABCD",
                     "flavor": "xxx.smallest",
                     "neighbours": ["ted", "john", "mickie"],
                     "count": 5}

        testee = self.SheldonBeatsDoctor(member="bar", dictionary=cool_dict)
        self.assertEquals({'member': 'bar', 'dictionary': cool_dict},
                          testee.to_dict())

    def test_formatters(self):
        testee = self.SheldonBeatsDoctor(member="bar", b='evil password')
        self.assertEquals({'member': 'bar', 'b': 'bazzinga!'},
                          testee.to_dict())

    def test_parsers(self):
        testee = self.SheldonBeatsDoctor.to_object(a='birma')
        self.assertEquals('sheldon', testee.a)

    def test_no_more_objects(self):
        class Wrong(object):
            pass

        testee = self.SheldonBeatsDoctor(member=Wrong())
        self.assertRaises(NotImplementedError, testee.to_dict)
