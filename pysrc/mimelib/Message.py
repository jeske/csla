# Copyright (C) 2001 Python Software Foundation

"""Basic message object for the mimelib object model.
"""

import re
import address
from types import ListType

SEMISPACE = '; '

import Errors



class Message:
    """Basic message object for use inside the object tree.

    A message object is defined as something that has a bunch of rfc822
    headers and a payload.  If the body of the message is a multipart, then
    the payload is a list of Messages, otherwise it is a string.

    These objects implement part of the `mapping' interface, which assumes
    there is exactly one occurrance of the header per message.  Some headers
    do in fact appear multiple times (e.g. Received:) and for those headers,
    you must use the explicit API to set or get all the headers.  Not all of
    the mapping methods are implemented.

    """
    def __init__(self):
        self._headers = []
        self._unixfrom = None
        self._payload = None

    def ismultipart(self):
        """Return true if the message consists of multiple parts."""
        if type(self._payload) is ListType:
            return 1
        return 0

    #
    # Unix From_ line
    #
    def set_unixfrom(self, unixfrom):
        self._unixfrom = unixfrom

    def get_unixfrom(self):
        return self._unixfrom

    #
    # Payload manipulation.
    #
    def add_payload(self, payload, strict=1):
        """Add the given payload to the current payload.

        If the current payload is empty, then the current payload will be made
        a scalar, set to the given value.
        """
        if self._payload is None:
            self._payload = payload
        elif type(self._payload) is ListType:
            self._payload.append(payload)
        elif strict and self.getmaintype() not in (None, 'multipart'):
            raise Errors.MultipartConversionError(
                'Message main Content-Type: must be "multipart" or missing, not "%s"' % self.getmaintype())
        else:
            self._payload = [self._payload, payload]

    def get_payload(self, i=None):
        """Return the current payload exactly as is.

        Optional i returns that index into the payload.
        """
        if i is None:
            return self._payload
        if type(self._payload) is not ListType:
            raise TypeError, i
        return self._payload[i]

    def set_payload(self, payload):
        """Set the payload to the given value."""
        self._payload = payload

    #
    # MAPPING INTERFACE (partial)
    #
    def __len__(self):
        """Get the total number of headers, including duplicates."""
        return len(self._headers)

    def __getitem__(self, name):
        """Get a header value.

        Return None if the header is missing instead of raising an exception.

        Note that if the header appeared multiple times, exactly which
        occurrance gets returned is undefined.  Use getall() to get all
        the values matching a header field name.
        """
        return self.get(name)

    def __setitem__(self, name, val):
        """Set the value of a header.

        Note: this does not overwrite an existing header with the same field
        name.  Use __delitem__() first to delete any existing headers.
        """
        self._headers.append((name, val))

    def __delitem__(self, name):
        """Delete all occurrences of a header, if present.

        Does not raise an exception if the header is missing.
        """
        name = name.lower()
        newheaders = []
        for k, v in self._headers:
            if k.lower() <> name:
                newheaders.append((k, v))
        self._headers = newheaders

    def has_key(self, name):
        """Return true if the message contains the header."""
        return self[name] <> None

    def keys(self):
        """Return a list of all the message's header field names.

        These will be sorted in the order they appeared in the original
        message, and may contain duplicates.  Any fields deleted and
        re-inserted are always appended to the header list.
        """
        return [k for k, v in self._headers]

    def values(self):
        """Return a list of all the message's header values.

        These will be sorted in the order they appeared in the original
        message, and may contain duplicates.  Any fields deleted and
        re-inserted are alwyas appended to the header list.
        """
        return [v for k, v in self._headers]

    def items(self):
        """Get all the message's header fields and values.

        These will be sorted in the order they appeared in the original
        message, and may contain duplicates.  Any fields deleted and
        re-inserted are alwyas appended to the header list.
        """
        return self._headers[:]

    def get(self, name, failobj=None):
        """Get a header value.

        Like __getitem__() but return failobj instead of None when the field
        is missing.
        """
        name = name.lower()
        for k, v in self._headers:
            if k.lower() == name:
                return v
        return failobj

    #
    # Additional useful stuff
    #

    def getall(self, name, failobj=None):
        """Return a list of all the values for the named field.

        These will be sorted in the order they appeared in the original
        message, and may contain duplicates.  Any fields deleted and
        re-inserted are alwyas appended to the header list.
        """
        values = []
        name = name.lower()
        for k, v in self._headers:
            if k.lower() == name:
                values.append(v)
        return values

    def addheader(self, _name, _value, **_params):
        """Extended header setting.

        name is the header field to add.  keyword arguments can be used to set
        additional parameters for the header field, with underscores converted
        to dashes.  Normally the parameter will be added as key="value" unless
        value is None, in which case only the key will be added.

        Example:

        msg.addheader('content-disposition', 'attachment', filename='bud.gif')

        """
        parts = []
        for k, v in _params.items():
            if v is None:
                parts.append(k.replace('_', '-'))
            else:
                parts.append('%s="%s"' % (k.replace('_', '-'), v))
        if _value is not None:
            parts.insert(0, _value)
        self._headers.append((_name, SEMISPACE.join(parts)))

    def gettype(self, failobj=None):
        """Returns the message's content type.

        The returned string is coerced to lowercase and returned as a single
        string of the form `maintype/subtype'.  If there was no Content-Type:
        header in the message, failobj is returned (defaults to None).
        """
        missing = []
        value = self.get('content-type', missing)
        if value is missing:
            return failobj
        return re.split(r';\s*', value.strip())[0].lower()

    def getmaintype(self, failobj=None):
        """Return the message's main content type if present."""
        missing = []
        ctype = self.gettype(missing)
        if ctype is missing:
            return failobj
        parts = ctype.split('/')
        if len(parts) > 0:
            return ctype.split('/')[0]
        return failobj

    def getsubtype(self, failobj=None):
        """Return the message's content subtype if present."""
        missing = []
        ctype = self.gettype(missing)
        if ctype is missing:
            return failobj
        parts = ctype.split('/')
        if len(parts) > 1:
            return ctype.split('/')[1]
        return failobj

    def getparams(self, failobj=None, header='content-type'):
        """Return the message's Content-Type: parameters, as a list.

        Optional failobj is the object to return if there is no Content-Type:
        header.  Optional header is the header to search instead of
        Content-Type:
        """
        missing = []
        value = self.get(header, missing)
        if value is missing:
            return failobj
        return re.split(r';\s*', value)[1:]

    def getparam(self, param, failobj=None, header='content-type'):
        """Return the parameter value if found in the Content-Type: header.

        Optional failobj is the object to return if there is no Content-Type:
        header.  Optional header is the header to search instead of
        Content-Type:
        """
        param = param.lower()
        missing = []
        params = self.getparams(missing, header=header)
        if params is missing:
            return failobj
        for p in params:
            try:
                name, val = p.split('=', 1)
            except ValueError:
                name = p
                val = None
            if name.lower() == param:
                return address.unquote(val)
        return failobj
