# Copyright (C) 2001 Python Software Foundation

"""Class for generating text/* type MIME documents.
"""

import MIMEBase
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


class Text(MIMEBase.MIMEBase):
    """Class for generating text/* type MIME documents."""

    def __init__(self, _text, _minor='plain', _charset="us-ascii"):
        """Create a text/* type MIME document.

        _text is the string for this message object.  If the text does not end
        in a newline, one is added.

        _minor is the minor content type, defaulting to "plain".

        _charset is the character set parameter added to the Content-Type:
        header.  This defaults to "us-ascii".
        """

        _charset = string.lower(_charset)
      
        enc = None
        cnt8 = count_nonascii (_text)
        # upgrade to iso-8859-1 if there are 8bit characters
        if cnt8 and _charset == "us-ascii":
            _charset = "iso-8859-1"
         
        # Which is shorter, base64 or qp?
        if cnt8:
            # the russians all have old clients which can't do mime decoding
            # apparently, Outlook for JP doesn't do line breaks correctly
            # if we base64 encode the message.  Technically, jis should be 
            # 7bit, but it will contain \027 <esc>... so we'll say 8bit
            if _charset in ['koi8-r', 'iso-2022-jp', 'iso-2022-kr']:
                enc = "8bit"
            elif len (_text) + cnt8 * 3 < len (_text) * 4 / 3:
                enc = "qp"
            else:
                enc = "base64"
        MIMEBase.MIMEBase.__init__(self, 'text', _minor,
                                   **{'charset': _charset})
        if _text and _text[-1] <> '\n':
            _text += '\n'
        self.set_payload(_text)
        if enc == "qp":
            qp_encoder(self)
        elif enc == "base64":
            base64_encoder(self)
        elif enc == "8bit":
            self['Content-Transfer-Encoding'] = '8bit'
