import unittest
import sys

from ZODB.utils import p64
from persistent import Persistent
from zope.app.testing import setup
from zope.interface.verify import verifyObject
from zope.interface import implements
from zope.component import adapts, provideAdapter

from zodbbrowser.interfaces import IValueRenderer
from zodbbrowser.value import (GenericValue, TupleValue, ListValue, DictValue,
                               PersistentValue)


class Frob(object):
    pass


class PersistentFrob(Persistent):
    _p_oid = p64(23)

    def __repr__(self):
        return '<PersistentFrob>'


class FrobRenderer(object):
    adapts(Frob)
    implements(IValueRenderer)

    def __init__(self, context):
        self.context = context

    def render(self, tid=None):
        if tid:
            return '<Frob [tid=%s]>' % tid
        else:
            return '<Frob>'


class TestGenericValue(unittest.TestCase):

    def test_interface_compliance(self):
        verifyObject(IValueRenderer, GenericValue(None))

    def test_simple_repr(self):
        for s in [None, '', 'xyzzy', '\x17', u'\u1234']:
            self.assertEquals(GenericValue(s).render(), repr(s))

    def test_html_quoting(self):
        self.assertEquals(GenericValue('<html>').render(),
                          "'&lt;html&gt;'")

    def test_truncation(self):
        self.assertEquals(GenericValue('a very long string').render(limit=10),
                          """'a very lo<span class="truncated">...</span>""")


class TestTupleValue(unittest.TestCase):

    def setUp(self):
        setup.placelessSetUp()
        provideAdapter(GenericValue)
        provideAdapter(FrobRenderer)

    def tearDown(self):
        setup.placelessTearDown()

    def test_interface_compliance(self):
        verifyObject(IValueRenderer, TupleValue(()))

    def test_empty_tuple(self):
        self.assertEquals(TupleValue(()).render(), '()')

    def test_single_item_tuple(self):
        self.assertEquals(TupleValue((Frob(), )).render(), '(<Frob>, )')

    def test_longer_tuples(self):
        self.assertEquals(TupleValue((1, Frob())).render(), '(1, <Frob>)')
        self.assertEquals(TupleValue((1, Frob(), 2)).render(),
                          '(1, <Frob>, 2)')

    def test_tid_is_preserved(self):
        self.assertEquals(TupleValue((Frob(), )).render(tid=42),
                          '(<Frob [tid=42]>, )')


class TestListValue(unittest.TestCase):

    def setUp(self):
        setup.placelessSetUp()
        provideAdapter(GenericValue)
        provideAdapter(FrobRenderer)

    def tearDown(self):
        setup.placelessTearDown()

    def test_interface_compliance(self):
        verifyObject(IValueRenderer, ListValue([]))

    def test_empty_list(self):
        self.assertEquals(ListValue([]).render(), '[]')

    def test_single_item_list(self):
        self.assertEquals(ListValue([Frob()]).render(), '[<Frob>]')

    def test_longer_lists(self):
        self.assertEquals(ListValue([1, Frob()]).render(), '[1, <Frob>]')
        self.assertEquals(ListValue([1, Frob(), 2]).render(),
                          '[1, <Frob>, 2]')

    def test_tid_is_preserved(self):
        self.assertEquals(ListValue([Frob()]).render(tid=42),
                          '[<Frob [tid=42]>]')


class TestDictValue(unittest.TestCase):

    def setUp(self):
        setup.placelessSetUp()
        provideAdapter(GenericValue)
        provideAdapter(FrobRenderer)

    def tearDown(self):
        setup.placelessTearDown()

    def test_interface_compliance(self):
        verifyObject(IValueRenderer, DictValue({}))

    def test_empty_dict(self):
        self.assertEquals(DictValue({}).render(), '{}')

    def test_single_item_dict(self):
        self.assertEquals(DictValue({1: Frob()}).render(),
                          '{1: <Frob>}')

    def test_longer_dicts(self):
        self.assertEquals(DictValue({1: Frob(), 2: 3}).render(),
                          '{1: <Frob>, 2: 3}')
        self.assertEquals(DictValue({1: Frob(), 2: Frob(), 3: 4}).render(),
                          '{1: <Frob>, 2: <Frob>, 3: 4}')

    def test_tid_is_preserved(self):
        self.assertEquals(DictValue({Frob(): Frob()}).render(tid=42),
                          '{<Frob [tid=42]>: <Frob [tid=42]>}')


class TestPersistentValue(unittest.TestCase):

    def setUp(self):
        setup.placelessSetUp()
        provideAdapter(GenericValue)

    def tearDown(self):
        setup.placelessTearDown()

    def test_interface_compliance(self):
        verifyObject(IValueRenderer, PersistentValue(None))

    def test_rendering(self):
        self.assertEquals(PersistentValue(PersistentFrob()).render(),
                  '<a href="@@zodbbrowser?oid=23">&lt;PersistentFrob&gt;</a>')

    def test_tid_is_preserved(self):
        renderer = PersistentValue(PersistentFrob())
        self.assertEquals(renderer.render(tid=p64(42)),
                  '<a href="@@zodbbrowser?oid=23&amp;tid=42">'
                          '&lt;PersistentFrob&gt;</a>')


def test_suite():
    this = sys.modules[__name__]
    return unittest.defaultTestLoader.loadTestsFromModule(this)
