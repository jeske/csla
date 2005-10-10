# Copyright (C) 2001 Python Software Foundation

import re

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

# intra-package imports
import Errors
import Message

bcre = re.compile('boundary\s*=\s*"?([^"]+)"?', re.IGNORECASE)
EMPTYSTRING = ''
NL = '\n'



class Parser:
    def __init__(self, _class=Message.Message):
        """Parser of RFC822 and MIME email messages.

        Creates an in-memory object tree representing the message, which can
        then be manipulated and turned over to a Generator to return the
        textual representation of the message.

        The string must be formatted as a block of rfc822 headers and header
        continuation lines, optionally preceeded by a `Unix-from' header.  The
        header block is terminated either by the end of the string or by a
        blank line.

        _class is the class to instantiate for new message objects when they
        must be created.  This class must have a constructor that can take
        zero arguments.  Default is Message.Message.
        """
        self._class = _class
        self._strict = 0

    def parse(self, fp):
        root = self._class()
        self._parse(root, 0, fp)
        return root

    def parsestr(self, text):
        root = self._class()
        self._parse(root, 0, StringIO(text))
        return root

    def _parse(self, container, lineno, fp):
        # Parse the headers
        lastheader = ''
        lastvalue = []
        while 1:
            line = fp.readline()[:-1]
            if not line or not line.strip():
                break
            lineno += 1
            # Check for initial Unix From_ line
            if line.startswith('From '):
                if lineno == 1:
                    container.set_unixfrom(line)
                    continue
                else:
                    if self._strict:
                      raise Errors.HeaderParseError(
                          'Unix-from in headers after first rfc822 header',
                          lineno)
                    else:
                      continue
            #
            # Header continuation line
            if line[0] in ' \t':
                if not lastheader:
                    raise Errors.HeaderParseError(
                        'Continuation line seen before first header',
                        lineno)
                lastvalue.append(line)
                continue
            # Normal, non-continuation header.  BAW: this should check to make
            # sure it's a legal header, e.g. doesn't contain spaces.  Also, we
            # should expose the header matching algorithm in the API, and
            # allow for a non-strict parsing mode (that ignores the line
            # instead of raising the exception).
            i = line.find(':')
            if i < 0:
                if self._strict:
                  raise Errors.HeaderParseError(
                    'Not a header, not a continuation', lineno)
            else:
              if lastheader:
                  container[lastheader] = NL.join(lastvalue)
              lastheader = line[:i]
              lastvalue = [line[i+1:].lstrip()]
        # Make sure we retain the last header
        if lastheader:
            container[lastheader] = NL.join(lastvalue)
        # Now parse the body.  Subclasses can override.
        self._parsebody(container, lineno, fp)

    def _parsebody(self, container, lineno, fp):
        # Now parse the body, but first split the payload on the content-type
        # boundary if present.
        boundary = isdigest = None
        ctype = container['content-type']
        if ctype:
            mo = bcre.search(ctype)
            if mo:
                boundary = mo.group(1)
            isdigest = container.gettype().lower() == 'multipart/digest'
        # If there's a boundary, split the payload text into its constituent
        # parts and parse each separately.  Otherwise, just parse the rest of
        # the body as a single message.  Note: any exceptions raised in the
        # recursive parse need to have their line numbers coerced.
        if boundary:
            preamble = epilogue = None
            # Split into subparts.  The first boundary we're looking for won't
            # have the leading newline since we're at the start of the body
            # text.
            separator = '--' + boundary
            payload = fp.read()
            start = payload.find(separator)
            if start < 0:
                if self._strict:
                    raise Errors.BoundaryError(
                        "Couldn't find starting boundary", lineno)
                container.add_payload(payload, strict=self._strict)
                return
            if start > 0:
                # there's some pre-MIME boundary preamble
                preamble = payload[0:start]
            start += len(separator) + 1 + isdigest
            terminator = payload.find('\n' + separator + '--', start)
            if terminator < 0:
                if self._strict:
                  raise Errors.BoundaryError(
                      "Couldn't find terminating boundary",
                      lineno+payload.count('\n'))
                else:
                  # Search for last separator
                  terminator = payload.rfind('\n' + separator)
                  if terminator < 0:
                    terminator = len(payload)
            if terminator+len(separator)+3 < len(payload):
                # there's some post-MIME boundary epilogue
                epilogue = payload[terminator+len(separator)+3:]
            # We split the textual payload on the boundary separator, which
            # includes the trailing newline.  If the container is a
            # multipart/digest then the subparts are by default message/rfc822
            # instead of text/plain.  In that case, they'll have an extra
            # newline before the headers to distinguish the message's headers
            # from the subpart headers.
            if isdigest:
                separator += '\n\n'
            else:
                separator += '\n'
            parts = payload[start:terminator].split('\n' + separator)
            for part in parts:
                try:
                    msgobj = self.parsestr(part)
                except Errors.MessageError, e:
                    e += lineno
                    raise
                container.preamble = preamble
                container.epilogue = epilogue
                container.add_payload(msgobj, strict=self._strict)
        else:
            container.add_payload(fp.read(), strict=self._strict)
