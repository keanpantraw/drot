import json
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

    @drot.definition
    class Member(object):
        def __init__(self, field1=None, field2=None):
            self.field1 = field1
            self.field2 = field2

    BIG_DICT = {"member": {"field2": None,
                           "field1": [{"1": "2"}, {}]},
                "array": [1, 2, 3],
                "b": "bazzinga!",
                "dictionary": {"a": 100500},
                }

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

    def test_wrong_parser(self):
        try:
            @drot.parser(self.SheldonBeatsDoctor, 'a')
            def foo():
                pass
            raise RuntimeError("parser decorator forget "
                               "to check function signature!")
        except AssertionError:
            pass

    def test_wrong_formatter(self):
        try:
            @drot.formatter(self.SheldonBeatsDoctor, 'a')
            def foo():
                pass
            raise RuntimeError("formatter decorator forget "
                               "to check function signature!")
        except AssertionError:
            pass

    def test_wrong_class_for_parser(self):
        try:
            @drot.parser(int, 'foo')
            def foo(a):
                pass
            raise RuntimeError("parser decorator forget "
                               "to check class definition!")
        except AssertionError:
            pass

    def test_wrong_class_for_formatter(self):
        try:
            @drot.formatter(int, 'foo')
            def foo(a):
                pass
            raise RuntimeError("parser decorator forget "
                               "to check class definition!")
        except AssertionError:
            pass

    def test_to_json(self):

        member = self.Member(field1=[{'1': '2'}, {}], field2=None)
        testee = self.SheldonBeatsDoctor(array=[1, 2, 3],
                                         member=member,
                                         dictionary={'a': 100500},
                                         b='grizzly')

        self.assertEquals(self.BIG_DICT, json.loads(testee.to_json()))

    def test_from_json(self):
        try:
            @drot.parser(self.SheldonBeatsDoctor, 'member')
            def parse_member(value):
                return self.Member(**value)

            d = json.dumps(self.BIG_DICT)
            testee = self.SheldonBeatsDoctor.from_json(d)

            self.assertEquals([{'1': '2'}, {}], testee.member.field1)
            self.assertEquals([1, 2, 3], testee.array)
            self.assertEquals('bazzinga!', testee.b)
        finally:
            del getattr(self.SheldonBeatsDoctor, '__drot_parsers')['member']

    def test_excluded(self):
        testee = self.SheldonBeatsDoctor.to_object(**self.BIG_DICT)

        self.assertFalse('member' in testee.to_dict(excluded=['member']))
        self.assertTrue('member' in testee.to_dict())

    def test_array_cycle(self):
        L = [1, 2, 3]
        L.append(L)
        testee = self.SheldonBeatsDoctor(array=L)

        self.assertRaises(ValueError, testee.to_dict)

    def test_dictionary_cycle(self):
        D = {'a': 'b'}
        D['c'] = D
        testee = self.SheldonBeatsDoctor(dictionary=D)

        self.assertRaises(ValueError, testee.to_dict)

    def test_object_cycle(self):
        member = self.Member(field1=1)
        member.field1 = member
        testee = self.SheldonBeatsDoctor(member=member, array=2)

        self.assertRaises(ValueError, testee.to_dict)

    def test_complicated_cycle(self):
        member = self.Member(field1={})
        member.field1['bra'] = [1, 2, 3]
        member.field1['bra'].append(member)
        testee = self.SheldonBeatsDoctor(member=member, array=[])

        self.assertRaises(ValueError, testee.to_dict)

    def test_false_positive_cycle(self):
        s = "foo"
        l = []
        member = self.Member(field1=1)
        self.SheldonBeatsDoctor(array=[l, l, l]).to_dict()
        self.SheldonBeatsDoctor(member=member, array=member).to_dict()
        self.SheldonBeatsDoctor(dictionary={'a': s, 'b': s}).to_dict()
        member = self.Member(field1=l, field2=l)
        self.SheldonBeatsDoctor(member=member)


@drot.parser(DrotTestCase.SheldonBeatsDoctor, 'a')
def parse_a(value):
    return "sheldon"


@drot.formatter(DrotTestCase.SheldonBeatsDoctor, 'b')
def format_b(value):
    return "bazzinga!"
