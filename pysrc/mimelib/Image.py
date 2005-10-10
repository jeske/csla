# Copyright (C) 2001 Python Software Foundation

"""Class for generating image/* type MIME documents.
"""

import base64
import imghdr

import MIMEBase
import Errors



def base64_encoder(msg):
    """Base64 is the standard encoder for image data."""
    orig = msg.get_payload()
    encdata = base64.encodestring(orig)
    msg.set_payload(encdata)
    msg['Content-Transfer-Encoding'] = 'base64'



class Image(MIMEBase.MIMEBase):
    """Class for generating image/* type MIME documents."""

    def __init__(self, _imagedata, _minor=None,
                 _encoder=base64_encoder, **_params):
        """Create an image/* type MIME document.

        _imagedata is a string containing the raw image data.  If this data
        can be decoded by the standard Python `imghdr' module, then the
        subtype will be automatically included in the Content-Type: header.
        Otherwise, you can specify the specific image subtype via the _minor
        parameter.

        _encoder is a function which will perform the actual encoding for
        transport of the image data.  It takes one argument, which is this
        Image instance.  It should use get_payload() and set_payload() to
        change the payload to the encoded form.  It should also add any
        Content-Transfer-Encoding: or other headers to the message as
        necessary.  The default encoding is Base64.

        Any additional keyword arguments are passed to the base class
        constructor, which turns them into parameters on the Content-Type:
        header.
        """
        if _minor is None:
            _minor = imghdr.what(None, _imagedata)
        if _minor is None:
            raise TypeError, 'Could not guess image _minor type'
        MIMEBase.MIMEBase.__init__(self, 'image', _minor, **_params)
        self.set_payload(_imagedata)
        _encoder(self)
