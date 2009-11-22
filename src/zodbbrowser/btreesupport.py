"""
BTrees are commonly used in the Zope world.  This modules exposes the
contents of BTrees nicely, abstracting away the implementation details.

In the DB, every BTree can be represented by more than one persistent object,
every one of those versioned separately.  This is part of what makes BTrees
efficient.

The format of the picked BTree state is nicely documented in ZODB's source
code, specifically, BTreeTemplate.c and BucketTemplate.c.
"""

from BTrees.OOBTree import OOBTree
from zope.component import adapts, getMultiAdapter
from zope.interface import implements

# be compatible with Zope 3.4, but prefer the modern package structure
try:
    from zope.container.folder import Folder
except ImportError:
    from zope.app.folder import Folder # BBB
try:
    from zope.container.btree import BTreeContainer
except ImportError:
    from zope.app.container.btree import BTreeContainer # BBB

from zodbbrowser.interfaces import IStateInterpreter, IObjectHistory
from zodbbrowser.history import ZodbObjectHistory
from zodbbrowser.state import _loadState # XXX ugly
from zodbbrowser.state import GenericState


class OOBTreeHistory(ZodbObjectHistory):
    adapts(OOBTree)
    implements(IObjectHistory)

    def _load(self):
        # find all objects (tree and buckets) that have ever participated in
        # this OOBTree
        queue = [self.obj]
        seen = set(self.obj._p_oid)
        history_of = {}
        while queue:
            obj = queue.pop(0)
            history = history_of[obj._p_oid] = ZodbObjectHistory(obj).history
            for d in history:
                state = obj._p_jar.oldstate(obj, d['tid'])
                if state and len(state) > 1:
                    bucket = state[1]
                    if bucket._p_oid not in seen:
                        queue.append(bucket)
                        seen.add(bucket._p_oid)
        # merge the histories of all objects
        by_tid = {}
        for h in history_of.values():
            for d in h:
                by_tid.setdefault(d['tid'], d)
        self.history = by_tid.values()
        self.history.sort(key=lambda d: d['tid'], reverse=True)


class OOBTreeState(object):
    """Non-empty OOBTrees have a complicated tuple structure."""
    adapts(OOBTree, tuple, None)
    implements(IStateInterpreter)

    def __init__(self, type, state, tid):
        self.btree = OOBTree()
        self.btree.__setstate__(state)
        self.state = state
        # Large btrees have more than one bucket; we have to load old states
        # to all of them.  See BTreeTemplate.c and BucketTemplate.c for
        # docs of the pickled state format.
        while state and len(state) > 1:
            bucket = state[1]
            state = _loadState(bucket, tid=tid).state
            bucket.__setstate__(state)

    def getName(self):
        return None

    def getParent(self):
        return None

    def listAttributes(self):
        return None

    def listItems(self):
        # make a copy, since we may be calling self.btree.__setstate__
        # before caller looks at the list
        return list(self.btree.items())

    def asDict(self):
        # make a copy, since we may be calling self.btree.__setstate__
        # before caller looks into the dict! e.g. when comparing two
        # state revisions
        return dict(self.btree)


class EmptyOOBTreeState(OOBTreeState):
    """Empty OOBTrees pickle to None."""
    adapts(OOBTree, type(None), None)
    implements(IStateInterpreter)


class FolderState(GenericState):
    """Convenient access to a Folder's items"""
    adapts(Folder, dict, None)

    def listItems(self):
        data = self.state.get('data')
        if not data:
            return []
        # data will be an OOBTree
        loadedstate = _loadState(data, tid=self.tid).state
        return getMultiAdapter((data, loadedstate, self.tid),
                               IStateInterpreter).listItems()


class BTreeContainerState(GenericState):
    """Convenient access to a BTreeContainer's items"""
    adapts(BTreeContainer, dict, None)

    def listItems(self):
        # This is not a typo; BTreeContainer really uses
        # _SampleContainer__data, for BBB
        data = self.state.get('_SampleContainer__data')
        if not data:
            return []
        # data will be an OOBTree
        loadedstate = _loadState(data, tid=self.tid).state
        return getMultiAdapter((data, loadedstate, self.tid),
                               IStateInterpreter).listItems()

