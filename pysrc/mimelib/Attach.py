# Copyright (C) 2001 Python Software Foundation

"""Class for generating text/* type MIME documents.
"""

import Message
import base64, string, MimeQPEnc

def base64_encoder(msg):
    """Base64 is the standard encoder for image data."""
    orig = msg.get_payload()
    encdata = base64.encodestring(orig)
    msg.set_payload(encdata)
    msg['Content-Transfer-Encoding'] = 'base64'

def qp_encoder(msg):
    orig = msg.get_payload()
    encdata = MimeQPEnc.encodeQPrfc2045(orig)
    msg.set_payload(encdata)
    msg['Content-Transfer-Encoding'] = 'quoted-printable'

def count_nonascii (str, check = 0):
  count = 0  
  for x in range (len (str)):    
    if ord(str[x]) > 127 or ord(str[x]) < 32:
      count = count + 1
      if check:
        return count
  return count


class Attach(Message.Message):
    """Class for generating text/* type MIME documents."""

    def __init__(self, _data, _type, **_params):
        """Create an attachment 

        _data is the data for this object.
        """

        enc = None
        cnt8 = count_nonascii (_data)

        if _type.find('/') != -1:
            major = _type[:_type.find('/')]
        else:
            major = _type
         
        # Which is shorter, base64 or qp?
        if major == "text" and len (_data) + cnt8 * 3 < len (_data) * 4 / 3:
            enc = "qp"
        else:
            enc = "base64"
        Message.Message.__init__(self)
        self.addheader('Content-Type', _type, **_params)
        self.set_payload(_data)
        if enc == "qp":
            qp_encoder(self)
        elif enc == "base64":
            base64_encoder(self)
        elif enc == "8bit":
            self['Content-Transfer-Encoding'] = '8bit'
