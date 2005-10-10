# Copyright (C) 2001 Python Software Foundation

# mimelib output generator class

import time
import re
import random
import sys

from types import ListType, StringType
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# intra-package imports
import Message
import Errors

SEMISPACE = '; '
BAR = '|'

fcre = re.compile(r'^From ', re.MULTILINE)



class Generator:
    """Generates output from a Message object tree.

    This basic generator writes the message to the given file object as plain
    text.

    """
    def __init__(self, outfp, mangle_from_=1):
        """Create the generator for message flattening.

        outfp is the output file-like object for writing the message to.  It
        must have a write() method.

        Optional mangle_from_ is a flag that, when true, escapes From_ lines
        in the body of the message by putting a `>' in front of them.
        """
        self._fp = outfp
        self._mangle_from_ = mangle_from_

    def write(self, msg, unixfrom=1):
        """Print the message object tree rooted at msg to the output file
        specified when the Generator instance was created.

        unixfrom is a flag that forces the printing of a Unix From_ delimiter
        before the first object in the message tree.  If the original message
        has no From_ delimiter, a `standard' one is crafted.  Set this to
        false to inhibit the printing of any From_ delimiter.

        Note that for subobjects, no From_ line is printed.
        """
        if unixfrom:
            ufrom = msg.get_unixfrom()
            if not ufrom:
                ufrom = 'From nobody ' + time.ctime(time.time())
            print >> self._fp, ufrom
        # Some useful state variables since we're not going to use recursion
        # to write all the subobjects.  We'll need a stack of containers, the
        # default Content-Type: for subobjects (usually text/plain, but
        # message/rfc822 for subparts of a multipart/digest), and other state
        # variables.
        text = self._flatten(msg, suppress=0)
        print >> self._fp, text

    # Non-public methods

    def _flatten(self, msg, suppress=1):
        s = StringIO()
        if msg.ismultipart() or msg.getmaintype() == 'multipart':
            if msg.getsubtype(failobj='mixed') == 'digest':
                default_subctype = 'message/rfc822'
            else:
                default_subctype = 'text/plain'
            # Flatten all the contained messages
            submsg_texts = []
            if msg.ismultipart():
                for submsg in msg.get_payload():
                    if isinstance(submsg, Message.Message):
                        submsg_texts.append(self._flatten(submsg))
                    else:
                        submsg_texts.append(submsg)
            else:
                # multipart with 1 part
                submsg_texts.append(self._flatten(msg.get_payload()))
            # Get the container's boundary
            boundary = msg.getparam('boundary')
            if boundary is None:
                boundary = self._makeboundary()
            # Make sure the container's boundary doesn't appear as a line in
            # any of the contained messages
            b = boundary
            while 1:
                cre = re.compile('^--' + re.escape(b) + '(--)?$',
                                 re.MULTILINE)
                for stext in submsg_texts:
                    if cre.search(stext):
                        if 'a' <= b[-1] < 'z':
                            b = b[:-1] + chr(ord(b[-1])+1)
                        else:
                            b += 'a'
                        break
                else:
                    break
            # Update the container's Content-Type: header
            boundary = b
            ctype = msg.gettype(failobj='multipart/mixed')
            del msg['content-type']
            msg.addheader('Content-Type', ctype, boundary=boundary)
            # Now glom up all the subobject texts into the flattened text for
            # this container message.  First, write the container's headers.
            self._writeheaders(msg, s, suppress)
            # Blank line separating headers and body
            print >> s
            # See if the original message has a preamble and epilogue
            preamble = getattr(msg, 'preamble', None)
            epilogue = getattr(msg, 'epilogue', None)
            if preamble:
                s.write(preamble)
            first = 1
            for stext in submsg_texts:
                # We need an extra newline preceding every boundary except the
                # first.
                if first: first = 0
                else:     print >> s
                print >> s, '--' + boundary
                # multipart/digest changes the default content type of the
                # subparts to message/rfc822, which require an extra newline
                # after the boundary so that the headers aren't mistaken for
                # part metadata.
                if default_subctype == 'message/rfc822':
                    print >> s
                s.write(stext)
            # Now write the trailing boundary, suppressing the extra newline
            # between this end-boundary and any subsequent starting boundary
            # for a sibling subpart.
            print >> s, '\n--' + boundary + '--',
            if epilogue:
                s.write(epilogue)
        # Is this an message/rfc822 encapsulated message?
        elif msg.getmaintype() == 'message':
            payload = msg.get_payload()
            self._writeheaders(msg, s, suppress)
            print >> s
            if isinstance(payload, Message.Message):
                s.write(self._flatten(payload))
            elif isinstance(payload, StringType):
                if self._mangle_from_:
                    payload = fcre.sub('>From ', payload)
                s.write(payload)
            else:
                raise TypeError, 'Message instance expected, %s found' % type(payload)
        # Not a multipart
        else:
            self._writeheaders(msg, s, suppress)
            # And the separating blank line
            print >> s
            # Escape From_
            payload = msg.get_payload()
            # The payload can be a string object, or if the content type is
            # message/rfc822, then it can be a message object
            if not isinstance(payload, StringType):
                raise TypeError, 'string expected, %s found' % type(payload)
            if self._mangle_from_:
                payload = fcre.sub('>From ', payload)
            s.write(payload)
        return s.getvalue()

    def _writeheaders(self, msg, fp, suppress):
        for h, v in msg.items():
            if h.lower() == 'mime-version' and suppress:
                continue
            else:
                print >> fp, h + ':', v
            
    def _makeboundary(self):
        # Craft a random and unlikely multipart/* boundary string
        return ('=' * 15) + repr(random.random()).split('.')[1] + '=='
