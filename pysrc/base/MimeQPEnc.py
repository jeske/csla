####
## MimeQPEnc.py
##
## A source conversion from Hiroyki Murata's Java 'MimeEnc' class
##

import sys
import string
import binascii
import base64
import re
import wordwrap

from log import log

try:
  import kconv
except:
  kconv = None

# Constants for kconv
kAUTO = 0
kJIS = 1
kEUC = 2
kSJIS = 3

rfc_2047_pat = re.compile(r"=\?"
                          r"(?P<charset>[^ ?]+?)"
                          r"\?"
                          r"(?P<encoding>[bBqQ])"
                          r"\?"
                          r"(?P<b64text>[^?]+?)"
                          r"\?=")

# this is so we don't see "half-truncated" rfc2047 strings!
truncated_rfc_2047_pat = re.compile(r"=\?"
                          r"[^ ]+"
                          r"[^?][^=]")


# another regexp for truncated rfc2047 strings
my_truncated_rfc_2047_pat = re.compile(r"(?P<start>.*?)"
                          r"=\?"
                          r"(?P<charset>[^ ?]+?)"
                          r"\?"
                          r"(?P<encoding>[bBqQ])"
                          r"\?"
                          r"(?P<b64text>[^?]+?)"
                          r"(\?=)?$")

def decodeSubject(subject_string):
  output, charset = rfc2047_decode (subject_string)

  return output

ecre = re.compile(r'''
  =\?                   # literal =?
  (?P<charset>[^?]*?)   # non-greedy up to the next ? is the charset
  \?                    # literal ?
  (?P<encoding>[qb])    # either a "q" or a "b", case insensitive
  \?                    # literal ?
  (?P<atom>.*?)         # non-greedy up to the next ?= is the atom
  \?=                   # literal ?=
  ''', re.VERBOSE | re.IGNORECASE)

def _bdecode(s):
    if not s:
        return s
    # We can't quite use base64.encodestring() since it tacks on a "courtesy
    # newline".  Blech!
    if not s:
        return s
    hasnewline = (s[-1] == '\n')
    value = base64.decodestring(s)
    if not hasnewline and value[-1] == '\n':
        return value[:-1]
    return value

try:
    import quopri

    def _qdecode(s):
        return quopri.decodestring(s, header=1)
except:
  def _qdecode(s):
      return decodeQPrfc2047str(s)

def _identity(s):
    return s

# assumes the whole string is in the same charset, which I haven't seen broken yet
def rfc2047_decode(s):
    """Return a decoded string according to RFC 2047, as a unicode string."""
    rtn = []
    found_decode = 0
    charset = None
    parts = ecre.split(s, 1)
    while parts:
        # If there are less than 4 parts, it can't be encoded and we're done
        if len(parts) < 5:
            rtn.extend(parts)
            break
        # The first element is any non-encoded leading text
        # ignore it if we're between encoded sections
        if found_decode == 0:
            rtn.append(parts[0])
        charset = string.lower(parts[1])
        encoding = parts[2].lower()
        atom = parts[3]
        # The next chunk to decode should be in parts[4]
        parts = ecre.split(parts[4])
        # The encoding must be either `q' or `b', case-insensitive
        if encoding == 'q':
            func = _qdecode
        elif encoding == 'b':
            func = _bdecode
        else:
            func = _identity
        # Decode and get the unicode in the charset
        rtn.append(func(atom))
        found_decode = 1
    # Now that we've decoded everything, we just need to join all the parts
    # together into the final string.
    return string.join(rtn,''), charset

def rfc2047_decode_old (enc_string):
  global rfc_2047_pat
  #log("enc_string: " + str(enc_string))  
  m = my_truncated_rfc_2047_pat.search(enc_string)
  if m:
      the_charset = string.lower(m.group('charset'))
  else:
      m = rfc_2047_pat.search(enc_string)
      if m:
        the_charset = string.lower(m.group('charset'))
      else:
        the_charset = None
  enc_string = rfc_2047_pat.sub(decodeQPrfc2047_re, enc_string)
  enc_string = my_truncated_rfc_2047_pat.sub(decodeQPrfc2047_re, enc_string)
  return enc_string, the_charset 
  #log("enc_string: " + str(enc_string))
  ## return subject_string
  #  return truncated_rfc_2047_pat.sub("--",subject_string)

  # try to decode truncated rfc2047 string for Japanese messages
  # a) base64-decode as much of the message as possible;
  #    (length of encoded string must be multiple of 4 bytes)
  # b) apply ISO-2022-JP-decoding to retrieve only whole multi-byte characters
  #
  # For non-japanese, just strip =?charset?q? part
  # 
  # Note: requires kconv to work properly
  m = my_truncated_rfc_2047_pat.search(enc_string)
  if m == None:
      return truncated_rfc_2047_pat.sub('', enc_string), the_charset

  output = m.group('start')
  the_charset = string.lower(m.group('charset'))
  the_encoding = string.lower(m.group('encoding'))
  if the_encoding != 'b':
      return output + m.group('b64text'), the_charset
  else:
      b64text = m.group('b64text')
      l = len(b64text)
      if l < 4:
          return output, the_charset
      b64text = b64text[0:((l / 4) * 4)]    # only multiples of 4 bytes
      output2 = []
      in_double = 0                         # double-byte mode flag
      i = 0

      try:
        remainder = base64.decodestring(b64text)
      except binascii.Error, reason:
        remainder = b64text
      if the_charset != 'iso-2022-jp':
          return (output+remainder), the_charset
      imax = len(remainder) - 1
      while i <= imax:
          if remainder[i:(i+3)] == _S1:	# start double-byte mode
              in_double = 1
              output2.append(_S1)
              i = i + 3
          elif remainder[i:(i+3)] == _S0:	# end double-byte mode
              in_double = 0
              output2.append(_S0)
              i = i + 3
          elif in_double == 0:              # in single-byte mode
              output2.append(remainder[i])
              i = i + 1
          elif i + 1 <= imax:               # in double-byte mode
              output2.append(remainder[i:(i+2)])
              i = i + 2
          else:                             # truncated double-byte char
              break

      if in_double:
          # if broke off in ending sequence, remove the partial sequence
          output2_len = len(output2) - 1
	  if output2[output2_len] == chr(0x1b) or output2[output2_len] == chr(0x1b)+ "(":
             output2 = output2[:output2_len]
          output2.append(_S0)                # end double-byte mode
      output2 = string.join(output2, '')
      output = output + output2
      return output, the_charset

def rfc2047_decode2 (enc_string):
  global rfc_2047_pat

  enc_string = rfc_2047_pat.sub(decodeQPrfc2047_re, enc_string)

  ## return subject_string
  #  return truncated_rfc_2047_pat.sub("--",subject_string)

  # try to decode truncated rfc2047 string for Japanese messages
  # a) base64-decode as much of the message as possible;
  #    (length of encoded string must be multiple of 4 bytes)
  # b) apply ISO-2022-JP-decoding to retrieve only whole multi-byte characters
  #
  # For non-japanese, just strip =?charset?q? part
  # 
  # Note: requires kconv to work properly
  m = my_truncated_rfc_2047_pat.match(enc_string)
  if m == None:
      return truncated_rfc_2047_pat.sub('', enc_string), None

  output = m.group('start')
  the_charset = string.lower(m.group('charset'))
  the_encoding = string.lower(m.group('encoding'))
  if the_charset != 'iso-2022-jp' or the_encoding != 'b':
      return output + m.group('b64text'), the_charset

  b64text = m.group('b64text')
  l = len(b64text)
  if l < 4:
      return output, the_charset
  b64text = b64text[0:((l / 4) * 4)]    # only multiples of 4 bytes
  output = []
  in_double = 0                         # double-byte mode flag
  i = 0
  try:
    remainder = base64.decodestring(b64text)
  except binascii.Error, reason:
    import handle_error
    handle_error.handleException()
    remainder = b64text

  imax = len(remainder) - 1
  while i <= imax:
      if remainder[i:(i+3)] == _S1:	# start double-byte mode
          in_double = 1
          output.append(_S1)
          i = i + 3
      elif remainder[i:(i+3)] == _S0:	# end double-byte mode
          in_double = 0
          output.append(_S0)
          i = i + 3
      elif in_double == 0:              # in single-byte mode
          output.append(remainder[i])
          i = i + 1
      elif i + 1 <= imax:               # in double-byte mode
          output.append(remainder[i:(i+1)])
          i = i + 2
      else:                             # truncated double-byte char
          break
  if in_double:
      output.append(_S0)                # end double-byte mode
  #log("output: " + str(output))
  output = string.join(output, '')
  return output, the_charset
  

#####################
## this is going to get tied to egroups pretty heavily
## here because I need to make sure it goes out in a
## valid charset! We should really do this a better
## way. - jeske
## 

def decodeQPrfc2047_re(matchobj):
  charset = string.lower(matchobj.group('charset'))
  encoding = string.lower(matchobj.group('encoding'))
  encstring   = matchobj.group('b64text')

  if encoding == "b":
    try:
      outstring = base64.decodestring(encstring)
    except binascii.Error, reason:
      import handle_error
      handle_error.handleException("bad base64")
      outstring = encstring
  elif encoding == "q":
    outstring = decodeQPrfc2047str(encstring)

  # this kconv stuff just plain does not work!
  # it does not listen to the output-format
  # that I ask for... - jeske
  # Um, seems to work for me -- blong
#  if charset == 'iso-2022-jp' and kconv:
#    outstring = kconv.convert(outstring, kSJIS) # convert to SJIS

  return outstring


_base64   = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
_mimehead = "=?ISO-2022-JP?B?"
_mimefoot = "?="

def encodeQPrfc2045(a_str, charset = None):
  if charset is None:
    charset = "ISO-8859-1"

  # ISO-8859-1 first
  escape_these = { '='   : None,   # None means use =XX encoding
                   '\r'  : '\r',   # encodes as itself
                   '\n'  : '\n',   # encodes as itself
                   ' '   : ' ',    # encodes as itself
                   '\t'  : '\t'}   # encodes as itself
                   
  output_string = ""
  line_len = 0

  for a_char in a_str:
    new_char = ""
    line_len = line_len + 1
    if line_len > 75:
      new_char = "=\r\n" # soft line break
      line_len = 0

    if escape_these.has_key(a_char):
      map_char = escape_these[a_char]
      if map_char is None:
        new_char = new_char + "=%02X" % ord(a_char)
      elif map_char in ['\n','\r']:
        line_len = 0
        new_char = new_char + map_char
      else:
        new_char = new_char + map_char
    elif (ord(a_char) < 33 or ord(a_char) > 126) or (ord(a_char) == 61):
      new_char = new_char + "=%02X" % ord(a_char)
    else:
      new_char = new_char + a_char

    output_string = output_string + new_char

  return output_string

  

def encodeQPrfc2047(a_str, charset = None):
  if charset is None:
    charset =  "ISO-8859-1"
  # ISO-8859-1 first
  escape_these = { '=': None,  # None means use = encoding
                   ' ':'_' ,   # space is special
                   '_': None,
                   '?': None,
                   '\t': None}

  output_string = "=?%s?q?" % charset # begin

  for a_char in a_str:
    if escape_these.has_key(a_char):
      new_char = escape_these[a_char]
      if new_char is None:
        new_char = "=%02X" % ord(a_char)
    elif ord(a_char) < 27 or ord(a_char) > 126:
      new_char = "=%02X" % ord(a_char)
    else:
      new_char = a_char

    output_string = output_string + new_char

  output_string = output_string + "?="  # end

  return output_string

# Ugh.  For ISO-2022-JP we have to ensure that every string has both a 
# start and end for double bit chars
_S1 = chr(0x1b) + "$" + "B"   # Start double byte
_S0 = chr(0x1b) + "(" + "B"   # End double byte
def correct_jp (line, in_double = 0):
  out = ""
  if in_double:
    if line[:3] != _S1:
      out = _S1
  for x in range (len (line)):
    if line[x] == chr(0x1b):
      if line[x:x+3] == _S1:
        in_double = 1
      elif line[x:x+3] == _S0:
        in_double = 0
  out = out + line
  if in_double:
    out = out + _S0

  return out, in_double

## Ugh very ugly, but we have to ensure that we don't break a double bit
## character in the middle
def encodeB64rfc2047_2022jp(a_str):
  charset =  "ISO-2022-JP"

  in_double = 0
  output_string = ""

  charset_string = "=?%s?B?" % charset # begin

  maxbinsize = 30 # ((40/4)*3)
  while a_str:
    x = 0
    enc = in_double
    slen = len (a_str)
    while (x < maxbinsize) and (x < slen):
      if a_str[x] == chr (0x1b):
        if a_str[x:x+3] == _S1:
          in_double = 1
          enc = 1
          x = x + 3 
          continue
        elif a_str[x:x+3] == _S0:
          in_double = 0
          x = x + 3 
          break
      if in_double:
        x = x + 2
      else:
        if ord(a_str[x]) < 32 or ord(a_str[x]) > 127:
          enc = 1
        x = x + 1
        if a_str[x-1] == ' ':
          break

    str = a_str[:x]
    a_str = a_str[x:]
    if in_double:
      str = str + _S0
      if a_str: a_str = _S1 + a_str
    if enc:
      output_string = "%s%s%s?= " % (output_string, charset_string, 
                                     string.strip(binascii.b2a_base64(str)))
    else:
      output_string = output_string + str


  return wordwrap.WordWrap (string.strip (output_string), cols=60, is_header=1)
  

def encodeB64rfc2047(a_str, charset = None):
  if not charset:
    charset = "ISO-8859-1"

  if string.lower (charset) == "iso-2022-jp":
    return encodeB64rfc2047_2022jp (a_str)

  output_string = ""

  charset_string = "=?%s?B?" % charset # begin

  maxbinsize = 30 # ((40/4)*3)
  while a_str:
    if (len (a_str) > maxbinsize):
      str = a_str[:maxbinsize]
      a_str = a_str[maxbinsize:]
    else:
      str = a_str
      a_str = None

    output_string = "%s%s%s?=\n " % (output_string, charset_string, 
                                     string.strip(binascii.b2a_base64(str)))

  return string.strip (output_string)

def encode_rfc2047 (a_str, charset = None):
  if not charset:
    charset = "ISO-8859-1"
  cnt8 = count_nonascii (a_str)
   
  # Which is shorter, base64 or qp?
  if string.lower (charset) not in ['iso-2022-jp','iso-2022-kr', 'euc-kr'] and \
      len (a_str) + cnt8 * 3 < len (a_str) * 4 / 3:
    return encodeQPrfc2047 (a_str, charset)
  else:
    return encodeB64rfc2047 (a_str, charset)


def decodeQPrfc2047str(a_str):
  output_string = ""
  
  strlen = len(a_str)
  pos = 0
  while pos < strlen:
    if a_str[pos] == "_":
      output_string = output_string + " "
      pos = pos + 1
    elif a_str[pos] == "=":
      if pos + 2 < strlen:
        atoi_str = a_str[pos+1:pos+3]
        # handle a bad value
        try:
          output_string = output_string + "%c" % (string.atoi(atoi_str,16),)
          pos = pos + 3
        except ValueError:
          pos = pos + 1
      else:
        pos = pos + 1
    else:
      output_string = output_string + a_str[pos]
      pos = pos + 1

  return output_string
      
## Utility Functions
def count_nonascii (str, check = 0):
  count = 0  
  for x in range (len (str)):    
    if ord(str[x]) > 127 or ord(str[x]) < 32:
      count = count + 1
      if check:
        return count
  return count

if __name__ == "__main__":

  def printHex(a_str):
    hex_str = ""
    for a_char in a_str:
      hex_str = hex_str + "%02X " % ord(a_char)

    print hex_str

  ## test QPrfc2047

  astring = "this is a test " + "%c" % 0x80 + " foo"
  cstring = encodeQPrfc2047(astring)

  print "raw: %s" % astring
  print "enc: %s" % cstring

  dstring = decodeSubject(cstring)
  if dstring != astring:
    print "conversion failed!"
    printHex(astring)
    printHex(dstring)
  else:
    print "conversion succeded!"
                                       


  ## test japanese string conversion

#  astring = r"受け取りました。"
  astring = r'グループへの登録をお申込みいただきありがとうございました。'
#  astring = astring + astring
#  astring = astring + astring
  estring = encodeB64rfc2047_2022jp(astring)
  print astring
  print estring

  
  try:
   import kconv
   lines = string.split (estring)
   print lines
   orig_str = ""
   for line in lines:
     orig_str = orig_str + kconv.convert(string.strip(line), kJIS)

   print orig_str

   passed = 1
   for pos in range(0,len(orig_str)):
     print "[%s] :   %s - %s" % (pos,ord(astring[pos]),ord(orig_str[pos]))
     if astring[pos] != orig_str[pos]:
       passed = 0
   if passed:
     print "Conversion PASSED!"
   else:
     print "Conversion corrupted string!" 
  except ImportError, reason:
    print "couldn't import kconv: %s" % reason
    print "Couldn't test back-conversion"
   
