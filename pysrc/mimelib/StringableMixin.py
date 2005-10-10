# Copyright (C) 2001 Python Software Foundation

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from Generator import Generator



class StringableMixin:
    """A mixin class which supports sensible str() and repr() semantics on
    Message objects.
    """
    def __str__(self):
        """Return the entire reproducible message.
        This includes the headers, body, and `unixfrom' line.
        """
        return self.get_text(unixfrom=1)

    def get_text(self, unixfrom=0):
        """Return the entire reproducible message.
        This includes the headers, body, and `unixfrom' line.
        """
        fp = StringIO()
        g = Generator(fp)
        g.write(self, unixfrom=unixfrom)
        return fp.getvalue()
