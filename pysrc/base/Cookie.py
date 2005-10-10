
####
#  by  Timothy O'Malley <timo@bbn.com> $Date: 2005/10/10 04:42:15 $
#
#  Cookie.py is an update for the old nscookie.py module.
#    Under the old module, it was not possible to set attributes,
#    such as "secure" or "Max-Age" on key,value granularity.  This
#    shortcoming has been addressed in Cookie.py but has come at
#    the cost of a slightly changed interface.  Cookie.py also
#    requires Python-1.5, for the re and cPickle modules.
#
#  The original idea to treat Cookies as a dictionary came from
#  Dave Mitchel (davem@magnet.com) in 1995, when he released the
#  first version of nscookie.py.
####

"""
Here's a sample session to show how to use this module.
At the moment, this is the only documentation.

Importing is easy..

   >>> import Cookie

Most of the time you start by creating a cookie.  The __init__
routine can take several arguments, but that isn't covered here.

   >>> C = Cookie.Cookie()

Now, you can add values to the Cookie just as is if it were a
dictionary.

   >>> C["joe"] = "a cookie"
   >>> C
   Set-Cookie: joe="a cookie";

Notice that the printable representation of a Cookie is the
appropriate format for a Set-Cookie: header.  This is the
default behavior.  You can change the header by using the
the .output() function

   >>> C.output("Cookie:")
   'Cookie: joe="a cookie";'


The .load() method of a Cookie extracts cookies from a string.  In
a CGI script, you would use this method to extract the cookies
from the HTTP_COOKIE environment variable.

   >>> C.load("mary=hadalittlelamb;")
   >>> C
   Set-Cookie: mary=hadalittlelamb;
   Set-Cookie: joe="a cookie";

Each element of the Cookie also supports all of the RFC 2109
Cookie attributes.  Here's an example which sets the Path
attribute.

   >>> C["joe"]["path"] = "/home/joe"
   >>> C
   Set-Cookie: mary=hadalittlelamb;
   Set-Cookie: joe="a cookie"; Path=/home/joe;

Before I forget, the .load() method is pretty smart about
identifying a cookie.  Escaped quotation marks and nested
semicolons do not confuse it.

   >>> C.load('lobotomy="joe=wolf; lobotomy=\\"nested quote\\"; mark=\\012;";')
   >>> C
   Set-Cookie: mary=hadalittlelamb;
   Set-Cookie: joe="a cookie"; Path=/home/joe;
   Set-Cookie: lobotomy="joe=wolf; lobotomy=\"nested quote\"; mark=\012;";


Each dictionary element has a 'value' attribute, which gives you
back the value associated with the key.

   >>> C["joe"].value
   'a cookie'
   >>> C["lobotomy"].value
   'joe=wolf; lobotomy="nested quote"; mark=\012;'

If you set a cookie to a non-string object, that object is
automatically pickled (using cPickle or pickle) in the
Set-Cookie: header.

   >>> C["int"] = 7
   >>> C
   Set-Cookie: lobotomy="joe=wolf; lobotomy=\"nested quote\"; mark=\012;";
   Set-Cookie: joe="a cookie"; Path=/home/joe;
   Set-Cookie: mary=hadalittlelamb;
   Set-Cookie: int="I7\012.";

If the .load() method finds a pickled object in the string, then
it automatically unpickles it.  The 'value' attribute gives you back
the true value, not the encoded representation.


   >>> C.load('anotherint="I45\\012.";')

   >>> C["anotherint"].value
   45
   >>> C["int"].value
   7

   >>> C
   Set-Cookie: lobotomy="joe=wolf; lobotomy=\"nested quote\"; mark=\012;";
   Set-Cookie: joe="a cookie"; Path=/home/joe;
   Set-Cookie: mary=hadalittlelamb;
   Set-Cookie: anotherint="I45\012.";
   Set-Cookie: int="I7\012.";

Finally, the encoding/decoding behavior is controllable by
two attributes of the Cookie:

  net_setfunc()    Takes in an encoded string and returns a value
  user_setfunc()   Takes in a value and returns the encoded string

By default, these functions are defined in the Cookie module, but
you should feel free to override them.

   >>> C.net_setfunc
   <function _debabelize at c1558>
   >>> C.user_setfunc
   <function _babelize at c1530>

Finis.
"""  #"
#     ^
#     |----helps out font-lock

#
# Import our required modules
#
import string, sys
from UserDict import UserDict
from log import *

import urllib

try:
    from cPickle import dumps, loads
except ImportError:
    from pickle import dumps, loads

try:
    import re
except ImportError:
    raise ImportError, "Cookie.py requires 're' from Python 1.5 or later"


#
# Define an exception visible to External modules
#
class CookieError(Exception):
    pass


# These quoting routines conform to the RFC2109 specification, which in
# turn references the character definitions from RFC2068.  They provide
# a two-way quoting algorithm.  Any non-text character is translated
# into a 4 character sequence: a forward-slash followed by the
# three-digit octal equivalent of the character.  Any '\' or '"' is
# quoted with a preceeding '\' slash.
# 
# These are taken from RFC2068 and RFC2109.
#       _LegalChars       is the list of chars which don't require "'s
#       _SpecialChars require the cookie to be double-quoted
#       _Translator       hash-table for fast quoting
#
_LegalChars       = string.letters + string.digits + "!#$%&'*+-.^_`|~"
_SpecialChars = string.translate(string._idmap, string._idmap, _LegalChars)
_Translator       = {
    '\000' : '\\000',  '\001' : '\\001',  '\002' : '\\002',  '\003' : '\\003',
    '\004' : '\\004',  '\005' : '\\005',  '\006' : '\\006',  '\007' : '\\007',
    '\010' : '\\010',  '\011' : '\\011',  '\012' : '\\012',  '\013' : '\\013',
    '\014' : '\\014',  '\015' : '\\015',  '\016' : '\\016',  '\017' : '\\017',
    '\020' : '\\020',  '\021' : '\\021',  '\022' : '\\022',  '\023' : '\\023',
    '\024' : '\\024',  '\025' : '\\025',  '\026' : '\\026',  '\027' : '\\027',
    '\030' : '\\030',  '\031' : '\\031',  '\032' : '\\032',  '\033' : '\\033',
    '\034' : '\\034',  '\035' : '\\035',  '\036' : '\\036',  '\037' : '\\037',
    ' ' : ' ',     '!' : '!',  '"' : '\\"',  '#' : '#',
    '$' : '$',     '%' : '%',  '&' : '&',    "'" : "'",
    '(' : '(',     ')' : ')',  '*' : '*',    '+' : '+',
    ',' : ',',     '-' : '-',   '.' : '.',   '/' : '/',
    '0' : '0',     '1' : '1',   '2' : '2',   '3' : '3',
    '4' : '4',     '5' : '5',   '6' : '6',   '7' : '7',
    '8' : '8',     '9' : '9',   ':' : ':',   ';' : ';',
    '<' : '<',     ':' : ':',   '>' : '>',   '?' : '?',
    '@' : '@',     'A' : 'A',   'B' : 'B',   'C' : 'C',
    'D' : 'D',     'E' : 'E',   'F' : 'F',   'G' : 'G',
    'H' : 'H',     'I' : 'I',   'J' : 'J',   'K' : 'K',
    'L' : 'L',     'M' : 'M',   'N' : 'N',   'O' : 'O',
    'P' : 'P',     'Q' : 'Q',   'R' : 'R',   'S' : 'S',
    'T' : 'T',     'U' : 'U',   'V' : 'V',   'W' : 'W',
    'X' : 'X',     'Y' : 'Y',   'Z' : 'Z',   '[' : '[',
    '\\' : '\\\\', ']' : ']',   '^' : '^',   '_' : '_',
    '=' : '\\074',
    '`' : '`',     'a' : 'a',   'b' : 'b',   'c' : 'c',
    'd' : 'd',     'e' : 'e',   'f' : 'f',   'g' : 'g',
    'h' : 'h',     'i' : 'i',   'j' : 'j',   'k' : 'k',
    'l' : 'l',     'm' : 'm',   'n' : 'n',   'o' : 'o',
    'p' : 'p',     'q' : 'q',   'r' : 'r',   's' : 's',
    't' : 't',     'u' : 'u',   'v' : 'v',   'w' : 'w',
    'x' : 'x',     'y' : 'y',   'z' : 'z',   '{' : '{',
    '|' : '|',     '}' : '}',   '~' : '~',   '\177' : '\\177',
    '\200' : '\\200',  '\201' : '\\201',  '\202' : '\\202',  '\203' : '\\203',
    '\204' : '\\204',  '\205' : '\\205',  '\206' : '\\206',  '\207' : '\\207',
    '\210' : '\\210',  '\211' : '\\211',  '\212' : '\\212',  '\213' : '\\213',
    '\214' : '\\214',  '\215' : '\\215',  '\216' : '\\216',  '\217' : '\\217',
    '\220' : '\\220',  '\221' : '\\221',  '\222' : '\\222',  '\223' : '\\223',
    '\224' : '\\224',  '\225' : '\\225',  '\226' : '\\226',  '\227' : '\\227',
    '\230' : '\\230',  '\231' : '\\231',  '\232' : '\\232',  '\233' : '\\233',
    '\234' : '\\234',  '\235' : '\\235',  '\236' : '\\236',  '\237' : '\\237',
    '\240' : '\\240',  '\241' : '\\241',  '\242' : '\\242',  '\243' : '\\243',
    '\244' : '\\244',  '\245' : '\\245',  '\246' : '\\246',  '\247' : '\\247',
    '\250' : '\\250',  '\251' : '\\251',  '\252' : '\\252',  '\253' : '\\253',
    '\254' : '\\254',  '\255' : '\\255',  '\256' : '\\256',  '\257' : '\\257',
    '\260' : '\\260',  '\261' : '\\261',  '\262' : '\\262',  '\263' : '\\263',
    '\264' : '\\264',  '\265' : '\\265',  '\266' : '\\266',  '\267' : '\\267',
    '\270' : '\\270',  '\271' : '\\271',  '\272' : '\\272',  '\273' : '\\273',
    '\274' : '\\274',  '\275' : '\\275',  '\276' : '\\276',  '\277' : '\\277',
    '\300' : '\\300',  '\301' : '\\301',  '\302' : '\\302',  '\303' : '\\303',
    '\304' : '\\304',  '\305' : '\\305',  '\306' : '\\306',  '\307' : '\\307',
    '\310' : '\\310',  '\311' : '\\311',  '\312' : '\\312',  '\313' : '\\313',
    '\314' : '\\314',  '\315' : '\\315',  '\316' : '\\316',  '\317' : '\\317',
    '\320' : '\\320',  '\321' : '\\321',  '\322' : '\\322',  '\323' : '\\323',
    '\324' : '\\324',  '\325' : '\\325',  '\326' : '\\326',  '\327' : '\\327',
    '\330' : '\\330',  '\331' : '\\331',  '\332' : '\\332',  '\333' : '\\333',
    '\334' : '\\334',  '\335' : '\\335',  '\336' : '\\336',  '\337' : '\\337',
    '\340' : '\\340',  '\341' : '\\341',  '\342' : '\\342',  '\343' : '\\343',
    '\344' : '\\344',  '\345' : '\\345',  '\346' : '\\346',  '\347' : '\\347',
    '\350' : '\\350',  '\351' : '\\351',  '\352' : '\\352',  '\353' : '\\353',
    '\354' : '\\354',  '\355' : '\\355',  '\356' : '\\356',  '\357' : '\\357',
    '\360' : '\\360',  '\361' : '\\361',  '\362' : '\\362',  '\363' : '\\363',
    '\364' : '\\364',  '\365' : '\\365',  '\366' : '\\366',  '\367' : '\\367',
    '\370' : '\\370',  '\371' : '\\371',  '\372' : '\\372',  '\373' : '\\373',
    '\374' : '\\374',  '\375' : '\\375',  '\376' : '\\376',  '\377' : '\\377'
    }

def _translate(c, table=_Translator):
    return table[c]

def _quote(str, join=string.join):
    # First check for common (and simple) case.
    #
    for C in _SpecialChars:
        if C in str:
            break
    else:
        return str

    # Ok, down to work.
    #    It's a shame we can't use _Translator.__getitem__
    #    but Python code doesn't have access to that function.
    #
    return '"' + join( map(_translate, str), "") + '"'
# end _quote


_OctalPatt = re.compile(r"\\[0-3][0-7][0-7]")
_QuotePatt = re.compile(r"[\\].")

def _unquote(str):
    # If there aren't any doublequotes,
    # then there can't be any special characters.  See RFC 2109.
    if  len(str) < 2:
        return str
    if str[0] != '"' or str[-1] != '"':
        return str

    # We have to assume that we must decode this string.
    # Down to work.

    # Remove the "s
    str = str[1:-1]
        
    # Check for special sequences.  Examples:
    #    \012 --> \n
    #    \"   --> "
    #
    i = 0
    n = len(str)
    res = []
    while 0 <= i < n:
        Omatch = _OctalPatt.search(str, i)
        Qmatch = _QuotePatt.search(str, i)
        if not Omatch and not Qmatch:              # Neither matched
            res.append(str[i:])
            break
        # else:
        j = k = -1
        if Omatch: j = Omatch.start(0)
        if Qmatch: k = Qmatch.start(0)
        if Qmatch and ( not Omatch or k < j ):     # QuotePatt matched
            res.append(str[i:k])
            res.append(str[k+1])
            i = k+2
        else:                                      # OctalPatt matched
            res.append(str[i:j])
            res.append( chr( string.atoi(str[j+1:j+4], 8) ) )
            i = j+4
    return string.join(res, "")
# end _unquote


# The _babelize() and _debabelize() functions allow arbitrary objects
# to be used as cookie values.  Large cookies may add significant
# overhead, because the client retransmits them on each visit.
#
# Note:  HTTP imposes a 2k limit on the size of cookie.  I don't check
# for this limit, so be careful!!!
#

def _babelize(val, dumps=dumps):
    if type(val) == type(""):
        return _quote(val)
    else:
        return _quote( dumps(val) )


def _debabelize(val, loads=loads):
    str = _unquote(val)
    if not str or str[-1] != ".": return str
    try:
        return loads(str)
    except:
        return str


# The _getdate() routine is used to set the expiration time in
# the cookie's HTTP header.      By default, _getdate() returns the
# current time in the appropriate "expires" format for a 
# Set-Cookie header.     The one optional argument is an offset from
# now, in seconds.      For example, an offset of -3600 means "one hour ago".
# The offset may be a floating point number.
#

_weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

_monthname = [None,
              'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def _getdate(future=0, weekdayname=_weekdayname, monthname=_monthname):
    from time import gmtime, time
    now = time()
    year, month, day, hh, mm, ss, wd, y, z = gmtime(now + future)
    return "%s, %02d-%3s-%4d %02d:%02d:%02d GMT" % \
           (weekdayname[wd], day, monthname[month], year, hh, mm, ss)

#
# Pattern for finding cookie
#
# This used to be strict parsing based on the RFC2109 and RFC2068
# specifications.  I have since discovered that MSIE 3.0x doesn't
# follow the character rules outlined in those specs.  As a
# result, the parsing rules here are less strict.
#

##_LegalCharsPatt  = r"[\w\d!#%&'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{]+"
_LegalCharsPatt  = r"[\w\d\n\r!#%'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{]+"
_SetCharsPatt  = r"[\, \w\d\n\r!#%'~_`><@,:/\$\*\+\-\.\^\|\)\(\?\}\{=&]+"
_CookiePattern = re.compile(
    r"(?x)"                       # This is a Verbose pattern
    r"(?P<key>"                   # Start of group 'key'
    ""+ _LegalCharsPatt +""         # Any word
    r")"                          # End of group 'key'
    r"("                        # second half optional start
    r"\s*=\s*"                    # Equal Sign
    r"(?P<val>"                   # Start of group 'val'
    r'"(?:[^\\"]|\\.)*"'            # Any doublequoted string
    r"|"                            # or
    ""+ _LegalCharsPatt +""         # Any word 
    r")"                          # End of group 'val'
    r"\s*"
    r")?"                       # second half optional end
    r";?"                      # Probably ending in a semi-colon
    )

_SetCookiePattern = re.compile(
    r"(?x)"                       # This is a Verbose pattern
    r"(?P<key>"                   # Start of group 'key'
    ""+ _LegalCharsPatt +""         # Any word
    r")"                          # End of group 'key'
    r"("                        # second half optional start
    r"\s*=\s*"                    # Equal Sign
    r"(?P<val>"                   # Start of group 'val'
    r'"(?:[^\\"]|\\.)*"'            # Any doublequoted string
    r"|"                            # or
    ""+ _SetCharsPatt +""         # Any word 
    r")"                          # End of group 'val'
    r"\s*"
    r")?"                       # second half optional end
    r";?"                      # Probably ending in a semi-colon
    )


#
# A class to hold ONE key,value pair.
# In a cookie, each such pair may have several attributes.
#       so this class is used to keep the attributes associated
#       with the appropriate key,value pair.
# This class also includes a coded_value attribute, which
#       is used to hold the network representation of the
#       value.  This is most useful when Python objects are
#       pickled for network transit.
#

class Morsel(UserDict):
    # RFC 2109 lists these attributes as reserved:
    #   path       comment         domain
    #   max-age    secure      version
    # 
    # For historical reasons, these attributes are also reserved:
    #   expires
    #
    # This dictionary provides a mapping from the lowercase
    # variant on the left to the appropriate Set-Cookie
    # format on the right.
    __reserved = { "expires" : "expires",
                   "path"        : "Path",
                   "comment" : "Comment",
                   "domain"      : "Domain",
                   "max-age" : "Max-Age",
                   "secure"      : "secure",
                   "version" : "Version",
                   }
    __reserved_keys = __reserved.keys()

    def __init__(self, input=None):
        # Set defaults
        self.key = self.value = self.coded_value = None
        UserDict.__init__(self)
        self._clear = 0
        self._header = None

        # Set default attributes
        for K in self.__reserved_keys:
            UserDict.__setitem__(self, K, "")
        if input:
          self.parse_set (input)
    # end __init__

      

    def __setitem__(self, K, V):
        K = string.lower(K)
        if not K in self.__reserved_keys:
            raise CookieError("Invalid Attribute %s" % K)
        UserDict.__setitem__(self, K, V)
    # end __setitem__

    def setitem(self, K, V):
        K = string.lower(K)
        if not K in self.__reserved_keys:
            raise CookieError("Invalid Attribute %s" % K)
        UserDict.__setitem__(self, K, V)
	d = self[K]


    # end __setitem__

    def set(self, key, val, coded_val):
        if string.lower(key) in self.__reserved_keys:
##            raise CookieError("Attempt to set a reserved key: %s" % key)
	  return
        self.key                 = key
        self.value               = val
        self.coded_value = coded_val
    # end set
    #
    def clearMorsel (self):
      self._clear = 1

    def output(self, header = "Set-Cookie:"):
        self._header = header
        return "%s %s" % ( header, self.OutputString() )
        self._header = None

    __repr__ = output

    def js_output(self):
        # Print javascript
        return """
        <SCRIPT LANGUAGE="JavaScript">
        <!-- begin hiding
        document.cookie = \"%s\"
        // end hiding -->
        </script>
        """ % ( self.OutputString(), )
    # end js_output()

    def OutputString(self):
        # Build up our result
        #
        result = []
        RA = result.append
        
        # First, the key=value pair
        RA('%s=%s;' % (self.key, self.coded_value))

        # Now add any defined attributes
        for K,V in self.items():
            if not V: continue
            if K == "expires" and type(V) == type(1):
                RA("%s=%s;" % (self.__reserved[K], _getdate(V)))
            if K == "max-age" and type(V) == type(1):
                RA("%s=%d;" % (self.__reserved[K], V))
            elif K == "secure":
                RA("%s;" % self.__reserved[K])
            else:
                RA("%s=%s;" % (self.__reserved[K], V))
        
        # Clear cookie hack, add all the domain
        if self._clear and self._header:
          if cookieClearMap.has_key (self['domain']):
            for domain in cookieClearMap[self['domain']]:
              RA("\n%s" % self._header)
              RA('%s=%s;' % (self.key, self.coded_value))
              for K,V in self.items():
                  if not V: continue
                  if K == "expires" and type(V) == type(1):
                      RA("%s=%s;" % (self.__reserved[K], _getdate(V)))
                  if K == "max-age" and type(V) == type(1):
                      RA("%s=%d;" % (self.__reserved[K], V))
                  elif K == "secure":
                      RA("%s;" % self.__reserved[K])
                  elif K == "domain":
                      RA("%s=%s;" % (self.__reserved[K], domain))
                  else:
                      RA("%s=%s;" % (self.__reserved[K], V))

          
        # Return the result
        return string.join(result, " ")
    # end OutputString
    #
    def parse_set (self, str, patt=_SetCookiePattern):
        ignore_list = {}
##         import os
## 	sys.stderr.write("url %s\n" % os.environ.get('SCRIPT_NAME', ''))
## 	sys.stderr.write("qs %s\n" % os.environ.get('QUERY_STRING', ''))
## 	sys.stderr.write("cookie %s\n" % str)
        log ("Morsel.parse_set (%s)" % str)

        i = 0            # Our starting point
        n = len(str)     # Length of string
        not_attr = 0     # value wasn't an attribute, start new Morsel

        while 0 <= i < n:
            # Start looking for a cookie
##	    sys.stderr.write("str: %s\n" % str)
            match = patt.search(str, i)
            if not match: break          # No more cookies

            K,V = match.group("key"), match.group("val")
            i = match.end(0)

            V = string.strip (V)
            # remember to ignore null cookies if they come up again
            if V is None:
                ignore_list[K] = 1
            # Our special "ignore this cookie" value
            if V == "XXXX":
                continue


##	    sys.stderr.write("%s %s\n" % (K,V))

            # For case where we're parsing a Set-Cookie, it'll
            # have attributes after the key, add them to the Morsel
            try:
              self[string.lower(K)] = V
              not_attr = 0
            except CookieError:
              not_attr = 1

            # Parse the key, value in case it's metainfo
            if K[0] == "$":
                not_attr = 0
                self[string.lower(K[1:])] = V
                # We ignore attributes which pertain to the cookie
                # mechanism as a whole.  See RFC 2109.
                # (Does anyone care?)
            if not_attr:
              if not self.key:
                self.set(K, apply(_debabelize, (V,)), V)
              else:
                raise CookieError("Invalid Attribute %s" % K)

    # end parse_set
# end Morsel class




# At long last, here is the cookie class.
#   Using this class is almost just like using a dictionary.
# See this module's docstring for example usage.
#
class Cookie(UserDict):
    # A container class for a set of Morsels
    #

    old_browser_re = None
        
    def __init__(self, input=None,
                 net_setfunc=_debabelize, user_setfunc=_babelize,
		 domain="", 
		 path="/", 
		 expires="Thu, 15 Apr 2010 20:00:00 GMT", maxage=31536000,
                 browser=""):
        self.net_setfunc   = net_setfunc   # when set from network
        self.user_setfunc  = user_setfunc  # when set by user
        UserDict.__init__(self)
        if input: self.load(input)

	self.domain = domain
	self.expires = expires
	self.path = path
        self.maxage = maxage
        self.browser = browser
        # Certain older browsers don't support setting of attributes
        # on cookies, at least not the new attributes like Max-Age
        # These browsers will probably break at Y2K as well, in which case
        # we need to stop sending an EXPIRE time based on this setting
        self.old_browser = 0
        if self.old_browser_re is None:
          self.old_browser_re = re.compile ("MSIE 3.0")
        m = self.old_browser_re.search (browser)
        if m:
          self.old_browser = 1

    # end __init__

    def __cmp__(self, dict):
      if type(dict) == type(self.data):
	return cmp(self.data, dict)
      elif dict == None:
	return -1
      else:
	return cmp(self.data, dict.data)



    def __setitem__(self, key, value):
        """Dictionary style assignment."""
        M = self.get(key, Morsel())
        M.set(key, value, apply(self.user_setfunc, (value,)))

	if self.domain: M['domain'] = self.domain
	if self.path: M['path'] = self.path
	if self.expires: M['expires'] = self.expires
        if not self.old_browser and self.maxage: M['max-age'] = self.maxage

        UserDict.__setitem__(self, key, M)

    def setitem(self, key, value, 
		    domain="", path="/", 
		    expires="Thu, 15 Apr 2010 20:00:00 GMT", maxage=None):
        """Dictionary style assignment."""
        M = self.get(key, Morsel())
        M.set(key, value, apply(self.user_setfunc, (value,)))

	if domain != "": M['domain'] = domain
        else: M['domain'] = self.domain
	if path: M['path'] = path
	if expires: M['expires'] = expires
        if not self.old_browser:
          if maxage == None:
            M['max-age'] = self.maxage
          else:
            M['max-age'] = maxage

        UserDict.__setitem__(self, key, M)

    # end __setitem__
    
    # Added by blong after he figured out how to finally clear a cookie
    # Apparently, you have to clear the value, and set the expires back
    # and ensure the domain is correct
    # the max-age is just to make sure
    def clearCookie (self, key):
      self.setitem(key, "", expires="Sat, 09-Nov-70 00:01:00 GMT")
      if not self.old_browser:
        self[key]['max-age'] = "0"
      M = self[key]
      M.clearMorsel()


    def output(self, header="Set-Cookie:"):
        """Return a string suitable for HTTP."""
        result = []
        for K,V in self.items():
            result.append( V.output(header) )
        return string.join(result,"\n")
    # end output

    __repr__ = output
        
    def js_output(self):
        """Return a string suitable for JavaScript."""
        result = []
        for K,V in self.items():
            result.append( V.js_output() )
        return string.join(result, "")
    # end js_output

    def load(self, rawdata):
        """Load cookies from a string (presumably HTTP_COOKIE) or
        from a dictionary.  Loading cookies from a dictionary 'd'
        is equivalent to calling:
            map(Cookie.__setitem__, d.keys(), d.values())
        Unfortunately, this does NOT allow merging of two Cookie
        dictionaries!
        """
        if type(rawdata) == type(""):
            self.__ParseString(rawdata)
        else:
            for K,V in rawdata.items():
                if not self.has_key(K):
                    self[K] = V
        return
    # end load()
        
    def __ParseString(self, str, patt=_CookiePattern):
        ignore_list = {}
##         import os
## 	sys.stderr.write("url %s\n" % os.environ.get('SCRIPT_NAME', ''))
## 	sys.stderr.write("qs %s\n" % os.environ.get('QUERY_STRING', ''))
## 	sys.stderr.write("cookie %s\n" % str)

        i = 0            # Our starting point
        n = len(str)     # Length of string
        M = None         # Current morsel
        not_attr = 0     # value wasn't an attribute, start new Morsel

        while 0 <= i < n:
            # Start looking for a cookie
##	    sys.stderr.write("str: %s\n" % str)
            match = patt.search(str, i)
            if not match: break          # No more cookies

            K,V = match.group("key"), match.group("val")
            i = match.end(0)

            # remember to ignore null cookies if they come up again
            if V is None:
                ignore_list[K] = 1

	    # don't do this!!
	    # sys.stderr.write("%s %s\n" % (K,V))
            #log("Cookie.py: %s %s" % (K,V))

            # For case where we're parsing a Set-Cookie, it'll
            # have attributes after the key, add them to the Morsel
            if M:
              try:
                M[string.lower(K)] = V
                not_attr = 0
              except CookieError:
                not_attr = 1

            if not M or not_attr:
              # Parse the key, value in case it's metainfo
              if K[0] == "$" and M:
                  M[string.lower(K[1:])] = V
                  # We ignore attributes which pertain to the cookie
                  # mechanism as a whole.  See RFC 2109.
                  # (Does anyone care?)
              elif not self.has_key(K) and not ignore_list.has_key(K):
                  M = Morsel()
                  M.set(K, apply(self.net_setfunc, (V,)), V)
                  UserDict.__setitem__(self, K, M)

    # end parse_set
    
# end Cookie class
