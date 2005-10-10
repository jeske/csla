# Copyright (C) 2001 Python Software Foundation

# mimelib exception classes

class MessageError(Exception):
    """Base class for errors in this module."""


class MessageParseError(MessageError):
    """Base class for message parsing errors."""
    def __init__(self, msg, lineno):
        self._msg = msg
        self._lineno = lineno

    def __str__(self):
        return self._msg + ' (line %d)' % self._lineno

    def __add__(self, other):
        return self._lineno + other

    def __sub__(self, other):
        return self._lineno - other

    def __iadd__(self, other):
        self._lineno += other

    def __isub__(self, other):
        self._lineno -= other


class HeaderParseError(MessageParseError):
    """Error while parsing headers."""


class BoundaryError(MessageParseError):
    """Couldn't find terminating boundary."""


class MultipartConversionError(MessageError, TypeError):
    """Conversion to a multipart is prohibited."""
