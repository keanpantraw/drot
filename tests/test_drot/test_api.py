import unittest

import drot


@drot.model()
class Member(object):
    field1 = None
    field2 = None


def parse_a(value):
    return "bazinga!"


@drot.model(a=parse_a, member=Member.to_object)
class TypicalModel(object):
    a = None
    b = None
    member = None
    array = None
    dictionary = None
    _c = None
    __d = None

    def foo(self, k):
        pass

    @classmethod
    def bar(self, tank):
        pass

    @property
    def prop(self):
        return "property"

    @prop.setter
    def set_prop(self, value):
        self.value = value


class DrotTestCase(unittest.TestCase):
    BIG_DICT = {"member": {"field2": None,
                           "field1": [{"1": "2"}, {}]},
                "array": [1, 2, 3],
                "b": "bazzinga!",
                "dictionary": {"a": 100500},
                }

    def test_some_values_are_set(self):
        testee = TypicalModel()
        testee.member = 'foo'
        self.assertEquals('foo', testee.to_dict()['member'])

    def test_array_is_set(self):
        testee = TypicalModel()
        testee.array = [1, 2, 3, 4]
        self.assertEquals([1, 2, 3, 4],
                          testee.to_dict()['array'])

    def test_dictionary_is_set(self):
        cool_dict = {"name": "instance-000ABCD",
                     "flavor": "xxx.smallest",
                     "neighbours": ["ted", "john", "mickie"],
                     "count": 5}

        testee = TypicalModel()
        testee.dictionary = cool_dict
        self.assertEquals(cool_dict,
                          testee.to_dict()['dictionary'])

    def test_no_more_objects(self):
        class Wrong(object):
            pass

        testee = TypicalModel()
        testee.member = Wrong()
        self.assertEquals(testee.member, testee.to_dict()['member'])

    def test_excluded(self):
        testee = TypicalModel.to_object(self.BIG_DICT)

        self.assertFalse('member' in testee.to_dict(excluded=['member']))
        self.assertTrue('member' in testee.to_dict())

    def test_array_cycle(self):
        L = [1, 2, 3]
        L.append(L)
        testee = TypicalModel()
        testee.array = L

        self.assertRaises(ValueError, testee.to_dict)

    def test_dictionary_cycle(self):
        D = {'a': 'b'}
        D['c'] = D
        testee = TypicalModel()
        testee.dictionary = D

        self.assertRaises(ValueError, testee.to_dict)

    def test_object_cycle(self):
        member = Member()
        member.field1 = member
        testee = TypicalModel()
        testee.member = member
        testee.array = 2

        self.assertRaises(ValueError, testee.to_dict)

    def test_complicated_cycle(self):
        member = Member()
        member.field1 = {}
        member.field1['bra'] = [1, 2, 3]
        member.field1['bra'].append(member)
        testee = TypicalModel()
        testee.member = member
        testee.array = []

        self.assertRaises(ValueError, testee.to_dict)

    def test_false_positive_cycle(self):
        s = "foo"
        l = []
        member = Member()
        member.field1 = 1
        testee = TypicalModel()

        testee.array = [l, l, l]
        testee.to_dict()

        testee.member = member
        testee.array = member
        testee.to_dict()

        testee.dictionary = {'a': s, 'b': s}
        testee.to_dict()

        member = Member()
        member.field1 = l
        member.field2 = l
        testee.member = member
        testee.to_dict()

        testee.dictionary = {'a': {'a': member,
                                   'b': {'b': member,
                                         'c': member}}}
        testee.to_dict()
