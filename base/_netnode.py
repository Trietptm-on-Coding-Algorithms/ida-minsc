"""
Netnode module (internal)

This module wraps IDA's netnode API and dumbs it down so that a user
can be mindless when reading/writing/enumerating data out of a netnode.
This is an internal module and is not expected to be used by the user.

TODO: Implement a wrapper around IDA's blob types so that we can simulate
      a filesystem.
"""

import six
import idaapi

import internal

MAXSPECSIZE = idaapi.MAXSTR
MAXNAMESIZE = idaapi.MAXNAMELEN

class netnode(object):
    try:
        # ida 6.95 splits up their idaapi module into smaller namespaces
        import _ida_netnode
    except ImportError:
        # _ida_netnode has got to be in at least one of these idaapi modules...
        import idaapi as _ida_netnode
        if not hasattr(idaapi, 'new_netnode'):
            import _idaapi as _ida_netnode

    new = _ida_netnode.new_netnode
    delete = _ida_netnode.delete_netnode
    start = _ida_netnode.netnode_start
    end = _ida_netnode.netnode_end
    index = _ida_netnode.netnode_index
    kill = _ida_netnode.netnode_kill
    long_value = _ida_netnode.netnode_long_value
    next = _ida_netnode.netnode_next
    prev = _ida_netnode.netnode_prev
    rename = _ida_netnode.netnode_rename
    #copyto = _ida_netnode.netnode_copyto
    #create = _ida_netnode.netnode_create
    #moveto = _ida_netnode.netnode_moveto
    set = _ida_netnode.netnode_set
    set_long = _ida_netnode.netnode_set_long
    delvalue = _ida_netnode.netnode_delvalue

    blobsize = _ida_netnode.netnode_blobsize
    getblob = _ida_netnode.netnode_getblob
    setblob = _ida_netnode.netnode_setblob
    delblob = _ida_netnode.netnode_delblob

    altdel = _ida_netnode.netnode_altdel
    altlast = _ida_netnode.netnode_altlast
    altprev = _ida_netnode.netnode_altprev
    altset = _ida_netnode.netnode_altset
    altval = _ida_netnode.netnode_altval

    charlast = _ida_netnode.netnode_charlast
    charprev = _ida_netnode.netnode_charprev
    chardel = _ida_netnode.netnode_chardel
    charset = _ida_netnode.netnode_charset
    charval = _ida_netnode.netnode_charval

    hashdel = _ida_netnode.netnode_hashdel
    hashlast = _ida_netnode.netnode_hashlast
    hashprev = _ida_netnode.netnode_hashprev
    hashset = _ida_netnode.netnode_hashset
    hashset_buf = _ida_netnode.netnode_hashset_buf
    hashset_idx = _ida_netnode.netnode_hashset_idx
    hashstr = _ida_netnode.netnode_hashstr
    hashstr_buf = _ida_netnode.netnode_hashstr_buf
    hashval = _ida_netnode.netnode_hashval
    hashval_long = _ida_netnode.netnode_hashval_long

    supdel = _ida_netnode.netnode_supdel
    suplast = _ida_netnode.netnode_suplast
    supprev = _ida_netnode.netnode_supprev
    supset = _ida_netnode.netnode_supset
    supstr = _ida_netnode.netnode_supstr
    supval = _ida_netnode.netnode_supval

    valobj = _ida_netnode.netnode_valobj
    valstr = _ida_netnode.netnode_valstr
    value_exists = _ida_netnode.netnode_value_exists

    # now to fix up the version skew as a result of IDA 7.0
    if idaapi.__version__ < 7.0:
        supfirst = _ida_netnode.netnode_sup1st
        supnext = _ida_netnode.netnode_supnxt
        hashnext = _ida_netnode.netnode_hashnxt
        hashfirst = _ida_netnode.netnode_hash1st
        charfirst = _ida_netnode.netnode_char1st
        charnext = _ida_netnode.netnode_charnxt
        name = _ida_netnode.netnode_name
        altfirst = _ida_netnode.netnode_alt1st
        altnext = _ida_netnode.netnode_altnxt

    else:   # >= 7.0
        supfirst = _ida_netnode.netnode_supfirst
        supnext = _ida_netnode.netnode_supnext
        hashnext = _ida_netnode.netnode_hashnext
        hashfirst = _ida_netnode.netnode_hashfirst
        charfirst = _ida_netnode.netnode_charfirst
        charnext = _ida_netnode.netnode_charnext
        name = _ida_netnode.netnode_get_name
        altfirst = _ida_netnode.netnode_altfirst
        altnext = _ida_netnode.netnode_altnext

class utils(object):
    @classmethod
    def range(cls):
        this = netnode.new()
        ok, start = netnode.start(this), netnode.index(this)
        if not ok: raise internal.exceptions.NetNodeNotFoundError(u"{:s}.range() : Unable to find first node.".format('.'.join([__name__, cls.__name__])))
        ok, end = netnode.end(this), netnode.index(this)
        if not ok: raise internal.exceptions.NetNodeNotFoundError(u"{:s}.range() : Unable to find end node.".format('.'.join([__name__, cls.__name__])))
        return start, end

    @classmethod
    def renumerate(cls):
        start, end = cls.range()
        this = netnode.new()
        ok = netnode.end(this)
        if not ok:
            raise internal.exceptions.NetNodeNotFoundError(u"{:s}.renumerate() : Unable to find the end node.".format('.'.join([__name__, cls.__name__])))

        yield end, netnode.new(end)
        while end != start:
            ok = netnode.prev(this)
            if not ok: break
            end = netnode.index(this)
            yield end, netnode.new(end)
        return

    @classmethod
    def fenumerate(cls):
        start, end = cls.range()
        this = netnode.new()
        ok = netnode.start(this)
        if not ok:
            raise internal.exceptions.NetNodeNotFoundError(u"{:s}.fenumerate() : Unable to find the start node.".format('.'.join([__name__, cls.__name__])))

        yield start, netnode.new(start)
        while start != end:
            ok = netnode.next(this)
            if not ok: break
            start = netnode.index(this)
            yield start, netnode.new(start)
        return

    @classmethod
    def valfiter(cls, node, first, last, next, val):
        start, end = first(node), last(node)
        if start in {None, idaapi.BADADDR}: return
        yield start, val(node, start)
        while start != end:
            start = next(node, start)
            yield start, val(node, start)
        return

    @classmethod
    def valriter(cls, node, first, last, prev, val):
        start, end = first(node), last(node)
        if end in {None, idaapi.BADADDR}: return
        yield end, val(node, end)
        while end != start:
            end = prev(node, end)
            yield end, val(node, end)
        return

    @classmethod
    def hfiter(cls, node, first, last, next, val):
        start, end = first(node), last(node)
        if val(node, start) is None: return
        yield start, val(node, start)
        while start != end:
            start = next(node, start)
            yield start, val(node, start)
        return

    @classmethod
    def hriter(cls, node, first, last, prev, val):
        start, end = first(node), last(node)
        if val(node, start) is None: return
        yield end, val(node, end)
        while end != start:
            end = prev(node, end)
            yield end, val(node, end)
        return

    @classmethod
    def falt(cls, node):
        for item in cls.valfiter(node, netnode.altfirst, netnode.altlast, netnode.altnext, netnode.altval):
            yield item
        return
    @classmethod
    def ralt(cls, node):
        for item in cls.valriter(node, netnode.altfirst, netnode.altprev, netnode.altnext, netnode.altval):
            yield item
        return

    @classmethod
    def fsup(cls, node):
        for item in cls.valfiter(node, netnode.supfirst, netnode.suplast, netnode.supnext, netnode.supval):
            yield item
        return
    @classmethod
    def rsup(cls, node):
        for item in cls.valriter(node, netnode.supfirst, netnode.supprev, netnode.supnext, netnode.supval):
            yield item
        return

    @classmethod
    def fhash(cls, node):
        for item in cls.hfiter(node, netnode.hashfirst, netnode.hashlast, netnode.hashnext, netnode.hashval):
            yield item
        return
    @classmethod
    def rhash(cls, node):
        for item in cls.hriter(node, netnode.hashfirst, netnode.hashprev, netnode.hashnext, netnode.hashval):
            yield item
        return

    @classmethod
    def fchar(cls, node):
        for item in cls.valfiter(node, netnode.charfirst, netnode.charlast, netnode.charnext, netnode.charval):
            yield item
        return
    @classmethod
    def rchar(cls, node):
        for item in cls.valriter(node, netnode.charfirst, netnode.charprev, netnode.charnext, netnode.charval):
            yield item
        return

def new(name):
    res = internal.utils.string.to(name)
    node = netnode.new(res, len(res), True)
    return netnode.index(node)

def get(name):
    if isinstance(name, six.integer_types):
        node = netnode.new(name)
        return netnode.index(node)
    res = internal.utils.string.to(name)
    node = netnode.new(res, len(res), False)
    return netnode.index(node)

def remove(nodeidx):
    node = netnode.new(nodeidx)
    return netnode.kill(node)

### node name
class name(object):
    @classmethod
    def get(cls, nodeidx):
        node = netnode.new(nodeidx)
        res = netnode.name(node)
        return internal.utils.string.of(res)
    @classmethod
    def set(cls, nodeidx, string):
        node = netnode.new(nodeidx)
        res = internal.utils.string.to(string)
        return netnode.rename(node, res)

### node value (?)
class value(object):
    @classmethod
    def exists(cls, nodeidx):
        node = netnode.new(nodeidx)
        return netnode.value_exists(node)

    @classmethod
    def get(cls, nodeidx, type=None):
        node = netnode.new(nodeidx)
        if not netnode.value_exists(node):
            return None

        if type in {None}:
            return netnode.valobj(node)
        elif issubclass(type, memoryview):
            res = netnode.valobj(node)
            return res and memoryview(res)
        elif issubclass(type, bytes):
            res = netnode.valstr(node)
            return res and bytes(res)
        elif issubclass(type, six.string_types):
            return netnode.valstr(node)
        elif issubclass(type, six.integer_types):
            return netnode.long_value(node)
        raise internal.exceptions.InvalidTypeOrValueError(u"{:s}.get({:#x}, type={!r}) : An unsupported type ({!r}) was requested for the netnode's value.".format('.'.join([__name__, cls.__name__]), nodeidx, type, type))

    @classmethod
    def set(cls, nodeidx, value):
        node = netnode.new(nodeidx)
        if isinstance(value, memoryview):
            return netnode.set(nodeidx, value.tobytes())
        elif isinstance(value, bytes):
            return netnode.set(node, value)
        elif isinstance(value, six.string_types):
            return netnode.set(node, value)
        elif isinstance(value, six.integer_types):
            return netnode.set_long(node, value)
        raise internal.exceptions.InvalidTypeOrValueError(u"{:s}.set({:#x}, {!r}) : An unsupported type ({!r}) was specified for the netnode's value.".format('.'.join([__name__, cls.__name__]), nodeidx, value, value.__class__))

    @classmethod
    def remove(cls, nodeidx, value):
        node = netnode.new(nodeidx)
        return netnode.delvalue(node)

    @classmethod
    def repr(cls, nodeidx):
        if not cls.exists(nodeidx):
            raise internal.exceptions.MissingTypeOrAttribute(u"{:s}.repr({:#x}) : The specified node ({:x}) does not have any value.".format('.'.join([__name__, cls.__name__]), nodeidx, nodeidx))
        res, string, value = cls.get(nodeidx), cls.get(nodeidx, type=bytes), cls.get(nodeidx, type=int)
        return "{!r} {!r} {:#x}".format(res, string, value)

### node blob
class blob(object):
    @classmethod
    def get(cls, nodeidx, tag, start=0):
        node = netnode.new(nodeidx)
        sz = netnode.blobsize(node, start, tag)
        res = netnode.getblob(node, start, tag)
        return None if res is None else res[:sz]

    @classmethod
    def set(cls, nodeidx, tag, value, start=0):
        node = netnode.new(nodeidx)
        return netnode.setblob(node, value.tobytes() if isinstance(value, memoryview) else value, start, tag)

    @classmethod
    def remove(cls, nodeidx, tag, start=0):
        node = netnode.new(nodeidx)
        return netnode.delblob(node, start, tag)

    @classmethod
    def size(cls, nodeidx, tag, start=0):
        node = netnode.new(nodeidx)
        return netnode.blobsize(node, start, tag)

    @classmethod
    def repr(cls, nodeidx, tag):
        if cls.size(nodeidx, tag) == 0:
            raise internal.exceptions.MissingTypeOrAttribute(u"{:s}.repr({:#x}, {!r}) : The tag {!r} for the specified node ({:x}) does not have a blob.".format('.'.join([__name__, cls.__name__]), nodeidx, tag, tag, nodeidx))
        res = cls.get(nodeidx, tag)
        return "{!r}".format(res)

### node iteration
def riter():
    for nodeidx, _ in utils.renumerate():
        yield nodeidx
    return
def fiter():
    for nodeidx, _ in utils.fenumerate():
        yield nodeidx
    return

### node altval iteration
class alt(object):
    '''Sparse array[int] of int'''
    @classmethod
    def get(cls, nodeidx, idx):
        node = netnode.new(nodeidx)
        return netnode.altval(node, idx)

    @classmethod
    def set(cls, nodeidx, idx, value):
        node = netnode.new(nodeidx)
        return netnode.altset(node, idx, value)

    @classmethod
    def remove(cls, nodeidx, idx):
        node = netnode.new(nodeidx)
        return netnode.altdel(node, idx)

    @classmethod
    def fiter(cls, nodeidx):
        node = netnode.new(nodeidx)
        for idx, value in utils.falt(node):
            yield idx, value
        return

    @classmethod
    def riter(cls, nodeidx):
        node = netnode.new(nodeidx)
        for idx, value in utils.ralt(node):
            yield idx, value
        return

    @classmethod
    def repr(cls, nodeidx):
        res = []
        for idx, value in cls.fiter(nodeidx):
            res.append("{0:x} : {1:#x} ({1:d})".format(idx, value))
        if not res:
            raise internal.exceptions.MissingTypeOrAttribute(u"{:s}.repr({:#x}) : The specified node ({:x}) does not have any altvals.".format('.'.join([__name__, cls.__name__]), nodeidx, nodeidx))
        return '\n'.join(res)

### node sup iteration
class sup(object):
    '''Sparse array[int] of 1024b strings'''

    MAX_SIZE = 0x400

    @classmethod
    def get(cls, nodeidx, idx, type=None):
        node = netnode.new(nodeidx)
        if type in {None}:
            return netnode.supval(node, idx)
        elif issubclass(type, memoryview):
            res = netnode.supval(node, idx)
            return res and memoryview(res)
        elif issubclass(type, bytes):
            return netnode.supstr(node, idx)
        elif issubclass(type, six.string_types):
            return netnode.supstr(node, idx)
        raise internal.exceptions.InvalidTypeOrValueError(u"{:s}.get({:#x}, {:#x}, type={!r}) : An unsupported type ({!r}) was requested for the netnode's supval.".format('.'.join([__name__, cls.__name__]), nodeidx, idx, type, type))

    @classmethod
    def set(cls, nodeidx, idx, value):
        node = netnode.new(nodeidx)
        return netnode.supset(node, idx, value.tobytes() if isinstance(value, memoryview) else value)

    @classmethod
    def remove(cls, nodeidx, idx):
        node = netnode.new(nodeidx)
        return netnode.supdel(node, idx)

    @classmethod
    def fiter(cls, nodeidx):
        node = netnode.new(nodeidx)
        for idx, _ in utils.fsup(node):
            yield idx
        return

    @classmethod
    def riter(cls, nodeidx):
        node = netnode.new(nodeidx)
        for idx, _ in utils.rsup(node):
            yield idx
        return

    @classmethod
    def repr(cls, nodeidx):
        res = []
        for idx, item in enumerate(cls.fiter(nodeidx)):
            value = cls.get(nodeidx, item)
            res.append("[{:d}] {:x} : {!r}".format(idx, item, value))
        if not res:
            raise internal.exceptions.MissingTypeOrAttribute(u"{:s}.repr({:#x}) : The specified node ({:x}) does not have any supvals.".format('.'.join([__name__, cls.__name__]), nodeidx, nodeidx))
        return '\n'.join(res)

### node hash iteration
class hash(object):
    '''Dictionary[char*510] of 1024b strings'''
    @classmethod
    def get(cls, nodeidx, key, type=None):
        node = netnode.new(nodeidx)
        if type in {None}:
            return netnode.hashval(node, key)
        elif issubclass(type, memoryview):
            res = netnode.hashval(node, key)
            return res and memoryview(res)
        elif issubclass(type, bytes):
            res = netnode.hashstr_buf(node, key)
            return res and bytes(res)
        elif issubclass(type, six.string_types):
            return netnode.hashstr(node, key)
        elif issubclass(type, six.integer_types):
            return netnode.hashval_long(node, key)
        raise internal.exceptions.InvalidTypeOrValueError(u"{:s}.get({:#x}, {!r}, type={!r}) : An unsupported type ({!r}) was requested for the netnode's hash.".format('.'.join([__name__, cls.__name__]), nodeidx, key, type, type))

    @classmethod
    def set(cls, nodeidx, key, value):
        node = netnode.new(nodeidx)
        # in my testing the type really doesn't matter
        if isinstance(value, memoryview):
            return netnode.hashset(node, key, value.tobytes())
        elif isinstance(value, bytes):
            return netnode.hashset_buf(node, key, value)
        elif isinstance(value, six.string_types):
            return netnode.hashset_buf(node, key, value)
        elif isinstance(value, six.integer_types):
            return netnode.hashset_idx(node, key, value)
        raise internal.exceptions.InvalidTypeOrValueError(u"{:s}.set({:#x}, {!r}, {!r}) : An unsupported type ({!r}) was specified for the netnode's hash.".format('.'.join([__name__, cls.__name__]), nodeidx, key, value, type(value)))

    @classmethod
    def remove(cls, nodeidx, key):
        node = netnode.new(nodeidx)
        return netnode.hashdel(node, key)

    @classmethod
    def fiter(cls, nodeidx):
        node = netnode.new(nodeidx)
        for key, _ in utils.fhash(node):
            yield key
        return

    @classmethod
    def riter(cls, nodeidx):
        node = netnode.new(nodeidx)
        for key, _ in utils.rhash(node):
            yield key
        return

    @classmethod
    def repr(cls, nodeidx):
        res = []
        try:
            l1 = max(len(key or '') for key in cls.fiter(nodeidx))
            l2 = max(len("{!r}".format(cls.get(nodeidx, key))) for key in cls.fiter(nodeidx))
        except ValueError:
            l1, l2 = 0, 2

        for idx, key in enumerate(cls.fiter(nodeidx)):
            value = "{:<{:d}s} : default={!r}, memoryview={!r}, bytes={!r}, int={:#x}({:d})".format("{!r}".format(cls.get(nodeidx, key)), l2, cls.get(nodeidx, key, None), cls.get(nodeidx, key, memoryview), cls.get(nodeidx, key, bytes), cls.get(nodeidx, key, int), cls.get(nodeidx, key, int))
            res.append("[{:d}] {:<{:d}s} -> {:s}".format(idx, key, l1, value))
        if not res:
            raise internal.exceptions.MissingTypeOrAttribute(u"{:s}.repr({:#x}) : The specified node ({:x}) does not have any hashvals.".format('.'.join([__name__, cls.__name__]), nodeidx, nodeidx))
        return '\n'.join(res)

# FIXME: implement a file-allocation-table based filesystem using the netnode wrappers defined above
class filesystem(object):
    ALLOCATION_TABLE = '$ file-allocation-table'
    SECTOR_TABLE = '$ sector-table'
    SECTOR = 1024
    def __init__(self, name):
        node = idaapi.netnode(name, 0, True)
