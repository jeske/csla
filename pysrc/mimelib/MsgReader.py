# Copyright (C) 2001 Python Software Foundation

"""Treat a message tree like a read-only file-like object.
"""

# TODO: Flesh out a more complete file-like method interface; add other
# traversal schemes such as "skip-any-non-text/plain-parts".

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from types import StringType



class MsgReader:
    """Depth-first traversal of body text with a readline() interface."""

    def __init__(self, rootmsg):
        self._root = rootmsg
        self._mstack = []
        self._payload = rootmsg.get_payload()
        self._fp = None
        self._pos = 0

    def readline(self):
##        import sys
##        from types import InstanceType
##        print >> sys.stderr, self._root.__class__.__name__, \
##              [p.__class__.__name__ for p in self._payload
##               if type(p) is InstanceType], \
##              self._pos
        if self._fp is None:
            if type(self._payload) is StringType:
                self._fp = StringIO(self._payload)
            else:
                if self._pos >= len(self._payload):
                    return ''
                self._mstack.append((self._root, self._payload, self._pos))
                self._root = self._payload[self._pos]
                self._payload = self._root.get_payload()
                self._pos = 0
                return self.readline()
        line = self._fp.readline()
        if not line:
            if not self._mstack:
                return ''
            self._root, self._payload, self._pos = self._mstack.pop()
            self._pos += 1
            self._fp = None
            return self.readline()
        return line

    def readlines(self, sizehint=None):
        bytes = 0
        lines = []
        while 1:
            line = self.readline()
            if not line:
                break
            lines.append(line)
            bytes += len(line)
            if sizehint is not None and bytes > sizehint:
                break
        return lines
