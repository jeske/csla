# Copyright (C) 2001 Python Software Foundation

# Address parsing class, taken straight out of rfc822.py

from rfc822 import unquote, quote, parseaddr
from rfc822 import dump_address_pair
from rfc822 import AddrlistClass as _AddrlistClass

COMMASPACE = ', '



def getaddresses(fieldvalues):
    all = COMMASPACE.join(fieldvalues)
    a = _AddrlistClass(all)
    return a.getaddrlist()
