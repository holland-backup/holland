"""
Tests for stuff in django.utils.datastructures.
"""
import pickle
import unittest

from copy import copy, deepcopy
from holland.core.util.datastructures import *


class DatastructuresTestCase(unittest.TestCase):
    def assertRaisesErrorWithMessage(self, error, message, callable,
        *args, **kwargs):
        self.assertRaises(error, callable, *args, **kwargs)
        try:
            callable(*args, **kwargs)
        except error, e:
            self.assertEqual(message, str(e))


class SortedDictTests(DatastructuresTestCase):
    def setUp(self):
        self.d1 = SortedDict()
        self.d1[7] = 'seven'
        self.d1[1] = 'one'
        self.d1[9] = 'nine'

        self.d2 = SortedDict()
        self.d2[1] = 'one'
        self.d2[9] = 'nine'
        self.d2[0] = 'nil'
        self.d2[7] = 'seven'

    def test_basic_methods(self):
        self.assertEquals(self.d1.keys(), [7, 1, 9])
        self.assertEquals(self.d1.values(), ['seven', 'one', 'nine'])
        self.assertEquals(self.d1.items(), [(7, 'seven'), (1, 'one'), (9, 'nine')])

        self.assertEquals([key for key in self.d1], [7, 1, 9])
        self.assertEquals([key for key in self.d1.iterkeys()], [7, 1, 9])
        self.assertEquals([value for value in self.d1.itervalues()],
                          ['seven', 'one', 'nine'])

        sd = SortedDict(self.d1)
        sd.insert(1, 6, 'six')
        self.assertEquals(sd.items(), [(7, 'seven'), (6, 'six'), (1, 'one'),
            (9, 'nine')])
        sd.insert(2, 7, 'seven')
        self.assertEquals(sd.items(), [(6, 'six'), (7, 'seven'), (1, 'one'), (9, 'nine')])

    def test_rename_key(self):
        sd = SortedDict(self.d1)

        sd.rename(9, 'NiNeR')
        self.assertEquals(sd.items(),
                          [(7, 'seven'), (1, 'one'), ('NiNeR', 'nine')])

        sd.rename(7, 'Sem')
        self.assertEquals(sd.items(),
                          [('Sem', 'seven'), (1, 'one'), ('NiNeR', 'nine')])

        sd.rename('Sem', 'seven')
        self.assertEquals(sd.items(),
                          [('seven', 'seven'), (1, 'one'), ('NiNeR', 'nine')])

    def test_overwrite_ordering(self):
        """ Overwriting an item keeps it's place. """
        self.d1[1] = 'ONE'
        self.assertEquals(self.d1.values(), ['seven', 'ONE', 'nine'])

    def test_append_items(self):
        """ New items go to the end. """
        self.d1[0] = 'nil'
        self.assertEquals(self.d1.keys(), [7, 1, 9, 0])

    def test_delete_and_insert(self):
        """
        Deleting an item, then inserting the same key again will place it
        at the end.
        """
        del self.d2[7]
        self.assertEquals(self.d2.keys(), [1, 9, 0])
        self.d2[7] = 'lucky number 7'
        self.assertEquals(self.d2.keys(), [1, 9, 0, 7])

    def test_change_keys(self):
        """
        Changing the keys won't do anything, it's only a copy of the
        keys dict.
        """
        k = self.d2.keys()
        k.remove(9)
        self.assertEquals(self.d2.keys(), [1, 9, 0, 7])

    def test_init_keys(self):
        """
        Initialising a SortedDict with two keys will just take the first one.

        A real dict will actually take the second value so we will too, but
        we'll keep the ordering from the first key found.
        """
        tuples = ((2, 'two'), (1, 'one'), (2, 'second-two'))
        d = SortedDict(tuples)

        self.assertEquals(d.keys(), [2, 1])

        real_dict = dict(tuples)
        self.assertEquals(sorted(real_dict.values()), ['one', 'second-two'])

        # Here the order of SortedDict values *is* what we are testing
        self.assertEquals(d.values(), ['second-two', 'one'])

    def test_overwrite(self):
        self.d1[1] = 'not one'
        self.assertEqual(self.d1[1], 'not one')
        self.assertEqual(self.d1.keys(), self.d1.copy().keys())

    def test_append(self):
        self.d1[13] = 'thirteen'
        self.assertEquals(
            repr(self.d1),
            "{7: 'seven', 1: 'one', 9: 'nine', 13: 'thirteen'}"
        )

    def test_pop(self):
        self.assertEquals(self.d1.pop(1, 'missing'), 'one')
        self.assertEquals(self.d1.pop(1, 'missing'), 'missing')

        # We don't know which item will be popped in popitem(), so we'll
        # just check that the number of keys has decreased.
        l = len(self.d1)
        self.d1.popitem()
        self.assertEquals(l - len(self.d1), 1)

    def test_dict_equality(self):
        d = SortedDict((i, i) for i in xrange(3))
        self.assertEquals(d, {0: 0, 1: 1, 2: 2})

    def test_tuple_init(self):
        d = SortedDict(((1, "one"), (0, "zero"), (2, "two")))
        self.assertEquals(repr(d), "{1: 'one', 0: 'zero', 2: 'two'}")

    def test_pickle(self):
        self.assertEquals(
            pickle.loads(pickle.dumps(self.d1, 2)),
            {7: 'seven', 1: 'one', 9: 'nine'}
        )

    def test_copy(self):
        from copy import deepcopy
        #XXX: check we're actually doing a deepcopy :P
        deepcopy(self.d1)

    def test_clear(self):
        self.d1.clear()
        self.assertEquals(self.d1, {})
        self.assertEquals(self.d1.keyOrder, [])

class MergeDictTests(DatastructuresTestCase):

    def test_simple_mergedict(self):
        d1 = {'chris':'cool', 'camri':'cute', 'cotton':'adorable',
              'tulip':'snuggable', 'twoofme':'firstone'}

        d2 = {'chris2':'cool2', 'camri2':'cute2', 'cotton2':'adorable2',
              'tulip2':'snuggable2'}

        d3 = {'chris3':'cool3', 'camri3':'cute3', 'cotton3':'adorable3',
              'tulip3':'snuggable3'}

        d4 = {'twoofme': 'secondone'}

        md = MergeDict(d1, d2, d3)

        self.assertEquals(md['chris2'], 'cool2')
        self.assertEquals(md['camri'], 'cute')
        self.assertEquals(md['twoofme'], 'firstone')
        self.assertRaises(KeyError, md.__getitem__, 'chris4')
        self.assertEquals(md.get('chris2'), 'cool2')
        self.assertEquals(md.get('chris4', 'cool4'), 'cool4')

        self.assertTrue(md.has_key('chris3'))
        self.assertFalse(md.has_key('twoofme3'))

        md2 = md.copy()
        self.assertEquals(md2['chris'], 'cool')

        self.assertEquals(str(md), str(dict(md.items())))
        self.assertEquals(repr(md), repr(md))

    def test_mergedict_merges_multivaluedict(self):
        """ MergeDict can merge MultiValueDicts """

        multi1 = MultiValueDict({'key1': ['value1'],
                                 'key2': ['value2', 'value3']})

        multi2 = MultiValueDict({'key2': ['value4'],
                                 'key4': ['value5', 'value6']})

        mm = MergeDict(multi1, multi2)

        # Although 'key2' appears in both dictionaries,
        # only the first value is used.
        self.assertEquals(mm.getlist('key2'), ['value2', 'value3'])
        self.assertEquals(mm.getlist('key4'), ['value5', 'value6'])
        self.assertEquals(mm.getlist('undefined'), [])

        self.assertEquals(sorted(mm.keys()), ['key1', 'key2', 'key4'])
        self.assertEquals(len(mm.values()), 3)

        self.assertTrue('value1' in mm.values())

        self.assertEquals(sorted(mm.items(), key=lambda k: k[0]),
                          [('key1', 'value1'), ('key2', 'value3'),
                           ('key4', 'value6')])

        self.assertEquals([(k,mm.getlist(k)) for k in sorted(mm)],
                          [('key1', ['value1']),
                           ('key2', ['value2', 'value3']),
                           ('key4', ['value5', 'value6'])])

class MultiValueDictTests(DatastructuresTestCase):

    def test_multivaluedict(self):
        d = MultiValueDict({'name': ['Adrian', 'Simon'],
                            'position': ['Developer']})

        self.assertEquals(d['name'], 'Simon')
        self.assertEquals(d.get('name'), 'Simon')
        self.assertEquals(d.getlist('name'), ['Adrian', 'Simon'])
        self.assertEquals(list(d.iteritems()),
                          [('position', 'Developer'), ('name', 'Simon')])

        self.assertEquals(list(d.iterlists()),
                          [('position', ['Developer']),
                           ('name', ['Adrian', 'Simon'])])

        # MultiValueDictKeyError: "Key 'lastname' not found in
        # <MultiValueDict: {'position': ['Developer'],
        #                   'name': ['Adrian', 'Simon']}>"
        self.assertRaisesErrorWithMessage(MultiValueDictKeyError,
            '"Key \'lastname\' not found in <MultiValueDict: {\'position\':'\
            ' [\'Developer\'], \'name\': [\'Adrian\', \'Simon\']}>"',
            d.__getitem__, 'lastname')

        self.assertEquals(d.get('lastname'), None)
        self.assertEquals(d.get('lastname', 'nonexistent'), 'nonexistent')
        self.assertEquals(d.getlist('lastname'), [])

        d.setlist('lastname', ['Holovaty', 'Willison'])
        self.assertEquals(d.getlist('lastname'), ['Holovaty', 'Willison'])
        self.assertEquals(d.values(), ['Developer', 'Simon', 'Willison'])
        self.assertEquals(list(d.itervalues()),
                          ['Developer', 'Simon', 'Willison'])

    def test_copy(self):
        for copy_func in [copy, lambda d: d.copy()]:
            d1 = MultiValueDict({
                "developers": ["Carl", "Fred"]
            })
            self.assertEqual(d1["developers"], "Fred")
            d2 = copy_func(d1)
            d2.update({"developers": "Groucho"})
            self.assertEqual(d2["developers"], "Groucho")
            self.assertEqual(d1["developers"], "Fred")

            d1 = MultiValueDict({
                "key": [[]]
            })
            self.assertEqual(d1["key"], [])
            d2 = copy_func(d1)
            d2["key"].append("Penguin")
            self.assertEqual(d1["key"], ["Penguin"])
            self.assertEqual(d2["key"], ["Penguin"])


class ImmutableListTests(DatastructuresTestCase):

    def test_sort(self):
        d = ImmutableList(range(10))

        # AttributeError: ImmutableList object is immutable.
        self.assertRaisesErrorWithMessage(AttributeError,
            'ImmutableList object is immutable.', d.sort)

        self.assertEquals(repr(d), '(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)')

    def test_custom_warning(self):
        d = ImmutableList(range(10), warning="Object is immutable!")

        self.assertEquals(d[1], 1)

        # AttributeError: Object is immutable!
        self.assertRaisesErrorWithMessage(AttributeError,
            'Object is immutable!', d.__setitem__, 1, 'test')

