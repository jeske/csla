
from types import ListType, StringType
import os, re, time

## Importing iconvcodec enables the iconv encoding/decoding
#import iconvcodec

from log import log
from mimelib import Message, Generator, Parser, date
from base.SafeHtml import SafeHtmlString
import neo_cgi
import string
from base import MimeQPEnc
import rfc822
import urllib

import msgrender

import htmlhelp

try:
    import kconv
except:
    kconv = None

try:
  from cStringIO import StringIO
except:
  from StringIO import StringIO

def maskAddr(addr):
  addr = re.sub("([^\s@<]+)@([^\s@]+\.[^\s@>]+)","\\1@...",addr)
  return addr

class RenderMessage:
  def __init__ (self, rawmsg = None,mimemsg = None, tz="US/Pacific"):
    self._charset = None
    self._tz = tz

    self.textrenderer = msgrender.TextToHtmlRender()

    if rawmsg:
      # fp = open("/tmp/email", "w")
      # fp.write(rawmsg)
      # fp.close()

      p = Parser.Parser()
      self.message = p.parsestr(rawmsg)

    else:
        if not mimemsg is None:
            self.message = mimemsg

  def part_name (self, m):
    if type(m) == type(""):
        return ""
    filename = m.getparam("name")
    if filename is None:
      filename = m.getparam("filename", header="Content-Disposition")
      if filename is None:
        filename = m.gettype("text/plain")
    output, charset = MimeQPEnc.rfc2047_decode (filename)
    if charset is None:
      ## Hack for those annoying Russians
      charset = self.charset(m)
    self._charset = charset
    return to_utf8 (output, charset)

  def charset (self, m, default='iso-8859-1'):
    # this does some funkiness to 'assume' that the entire
    # message has the same charset, but allow 'good' messages
    # that actually specify everything to get what they specify
    charset = m.getparam('charset', None)
    if charset is None:
        if self._charset is None:
            if m.ismultipart():
                for sm in m.get_payload():
                    charset = self.charset(sm, None)
                    if charset is not None: break
            elif m.getmaintype() == 'multipart':
                sm = m.get_payload()
                if type(sm) == type(m): 
                    charset = self.charset(sm, None)
        else:
            charset = self._charset
    self._charset = charset
    if charset is None: return default
    return charset

  def embedded_parts (self, m, url_str, urls={}, map_num = 0):
    # this does some funkiness to 'assume' that the entire
    # message has the same charset, but allow 'good' messages
    # that actually specify everything to get what they specify
    mtype = m.getmaintype()
    pname = self.part_name(m)
    x = string.rfind(pname, '.')
    if x != -1: ext = string.lower(pname[x:])
    else: ext = ''
    if mtype in ['image', 'audio', 'video'] or \
        ext in ['gif', 'jpg', 'jpeg', 'png', 'bmp']:
        cid = m.get('content-id', None)
        if not cid: return
        if cid[0] == '<' and cid[-1] == '>': cid = cid[1:-1]
        if cid:
            urls[cid] = url_str % ('%d:%s' % (map_num, pname))
        return
    else:
        if m.ismultipart():
            num = 0
            for sm in m.get_payload():
                self.embedded_parts(sm, url_str, urls, num)
                num = num + 1
        elif m.getmaintype() == 'multipart':
            sm = m.get_payload()
            if type(sm) == type(m): 
                self.embedded_parts(sm, url_str, urls)
    return 


  #########################
  #
  # fixbody(body_data)
  #
  # This function tries to fix bad things about email
  # bodies. 
  #
  def fixbody(self,raw_body):

    # FIX #1: reassemble broken URLs
    def fixurl(m):
      log("matched url: %s" % m.group(0))
      result = re.sub(" ?[\r\n]","",m.group(0))
      log("fixed url: %s" % result)
      return result

    raw_body = re.sub("[a-z]+://\S+(((/ ?\r?\n(?![a-z]{0,7}://))|( ?\r?\n/)|(- ?\r?\n))\S+)+(?= ?\r?\n)",
                       fixurl,raw_body)

    # FIX #2: space pad URLs which are surrounded by (), <> or []
    raw_body = re.sub("([<([])([a-z]+://[^ ]+)([>)\\]])","\\1 \\2 \\3",raw_body)

    # done with fixes
    return raw_body
 

  def attachments (self, m, parts=[], map_num = 0):
    if m.ismultipart():
        num = 0
        for sm in m.get_payload():
            self.attachments(sm, parts, num)
            num = num + 1
    elif m.getmaintype() == 'multipart':
        sm = m.get_payload()
        if type(sm) == type(m): 
            self.attachments(sm, parts)
    else:
        pname = self.part_name(m)
        parts.append(('%d:%s' % (map_num, pname), pname, m.gettype("text/plain"), map_num))
    return 

  # -----------
  # don't call this from outside here

  def export_part (self, m, prefix, hdf):
    punct = " ~`!@#$%^&*()-+=|}{[]\<>?,./:\";'" 
    trans = string.maketrans(punct, "_" * len(punct))
    n = 0
    for k, v in m.items():
        kn = string.upper(string.translate(k, trans))
        hdf.setValue("%s.Headers.%s" % (prefix, kn), v)
        hdf.setValue("%s.Headers.%s.name" % (prefix, kn), k)
        hdf.setValue("%s.Headers.%s.html" % (prefix, kn), neo_cgi.text2html(v))
        n = n + 1
    hdf.setValue("%s.HName" % (prefix), str(n))
    if m.ismultipart():
      if m.getsubtype("mixed") == "alternative":
        sub = []
        for sm in m.get_payload():
          st = sm.gettype("text/plain")
          if st == "text/html":
            sub.insert(0, sm)
          else:
            sub.append(sm)
        if sub:
          if sub[0].gettype("text/plain") == "text/html":
            body = SafeHtmlString(self.decode_part(sub[0], as_utf8 = 1), map_urls = self._urls)
            hdf.setValue ("%s.body" % prefix, body)
          elif sub[0].getmaintype("text") == "text":
            raw_body = self.decode_part(sub[0], as_utf8 = 1)
            raw_body = self.fixbody(raw_body)
            # body = neo_cgi.text2html(string.strip(raw_body))
            body = self.textrenderer.renderPlainTextToHtml(raw_body)
            hdf.setValue ("%s.body" % prefix, body)
      else:
        hdf.setValue ("%s.b_type" % prefix, "multipart")
        num = 0
        for sm in m.get_payload():
          hdf.setValue("%s.parts.%d.num" % (prefix,num),"%s" % num)
          self.export_part (sm, "%s.parts.%d" % (prefix, num), hdf)
          num = num+1
    else:
      ct = m.getmaintype("text")
      st = m.getsubtype("plain")
      filename = self.part_name (m)
      if filename:
        hdf.setValue ("%s.name" % prefix, urllib.quote(filename))
      if ct == "multipart":
        # annoying case where there aren't actually multiple parts in a 
        # multipart
        hdf.setValue ("%s.b_type" % prefix, "multipart")
        sm = m.get_payload()
        # I'm not entirely certain how this doesn't work...
        if type(sm) == type(m):
          hdf.setValue("%s.parts.0.num" % (prefix),"0")
          self.export_part (sm, "%s.parts.0" % (prefix), hdf)
      elif ct == "message":
        hdf.setValue ("%s.b_type" % prefix, "message")
        sm = m.get_payload()
        if type(sm) == StringType:
          p = Parser.Parser()
          sm = p.parsestr(sm)
        if type(sm) == type(m):
          hdf.setValue("%s.parts.0.num" % (prefix),"0")
          self.export_message ("%s.parts.0" % (prefix), hdf, sm)
      elif ct == "text":
        b = self.decode_part(m, as_utf8 = 1)
        if len(b) < 50000 and st == "html":
          body = SafeHtmlString(b, map_urls = self._urls)
          hdf.setValue ("%s.b_type" % prefix, "text")
          hdf.setValue ("%s.body" % prefix, body)
        elif len(b) < 50000 and st == "plain":
          hdf.setValue ("%s.b_type" % prefix, "text")
          b = self.fixbody(b)
          # converted_body = neo_cgi.text2html(string.strip(b))
          converted_body = self.textrenderer.renderPlainTextToHtml(b)
          if not converted_body is None:
            hdf.setValue ("%s.body" % prefix, converted_body)
        else:
          hdf.setValue ("%s.b_type" % prefix, "attach")
      elif ct == "image":
        hdf.setValue ("%s.b_type" % prefix, "image")
      else:
        hdf.setValue ("%s.b_type" % prefix, "attach")

  def decode_part (self, m, as_utf8 = 0):
    ct = m.getmaintype("text")
    if ct != "text": as_utf8 = 0
    body = m.get_payload()
    if not isinstance(body, StringType):
      body = str(body)
    encoding = string.lower(m.get('content-transfer-encoding', '7bit'))
    if encoding == "quoted-printable":
      from quopri import decode
      ## how annoying
      inb = StringIO(body)
      outb = StringIO()
      decode(inb, outb)
      body = outb.getvalue()
    elif encoding == "base64":
      from base64 import decodestring
      try:
        body = decodestring(body)
      except:
        pass
    if ct == "text":
      # don't allow embedded nulls in text parts
      body = string.replace(body, '\0', '')
    if as_utf8: return to_utf8(body, self.charset(m))
    return body

  def part_content (self, part, m = None):
    if m is None: m = self.message
    if part.find (':') == -1: return (None, None, part)
    (partnum, name) = part.split(':', 1)
    partnum = int(partnum)
    if m.ismultipart():
      if m.getsubtype("mixed") == "alternative":
        sub = []
        for sm in m.get_payload():
          st = sm.gettype("text/plain")
          if st == "text/html":
            sub.insert(0, sm)
          else:
            sub.append(sm)
        if sub and len(sub) > partnum:
          return sub[partnum].gettype("text/plain"), self.decode_part(sub[partnum]), name
      else:
        num = 0
        # hmm, this will have to recurse or something at some point...
        for sm in m.get_payload():
          if num == partnum and self.part_name(sm) == name:
            return sm.gettype("text/plain"), self.decode_part(sm), name
          num = num+1
    elif m.getmaintype() == 'multipart':
        sm = m.get_payload()
        if self.part_name(sm) == name:
          return sm.gettype("text/plain"), self.decode_part(sm), name
    else:
      if self.part_name(m) == name:
        return m.gettype("text/plain"), self.decode_part(m), name
    return None, None, name

  def decode_header (self, m, hdr, default='', as_utf8 = 0):
    val = m.get(hdr, default)
    if string.find(val, '\n') != -1:
        lines = string.split(val, '\n')
        lines = map(string.strip, lines)
        val = string.join(lines, ' ')
    output, charset = MimeQPEnc.rfc2047_decode (val)
    if charset is None:
      ## Hack for those annoying Russians
      charset = self.charset(m)
    self._charset = charset
    if as_utf8: return to_utf8 (output, charset)
    return output

  def export_address_header(self, prefix, hdf, m, header):
    data = self.decode_header(m, header, as_utf8 = 1)
    addrs = rfc822.AddressList(data)
    n = 0
    for (name, addr) in addrs:
        if not addr: continue
        addr = re.sub("\s([^\s@]+)@([^\s@]+\.[^\s@]+)","\\1@...",addr)
        if name:
            hdf.setValue("%s.%d.name" % (prefix, n), name)
            hdf.setValue("%s.%d.full" % (prefix, n), '"%s" <%s>' % (name, addr))
        else:
            hdf.setValue("%s.%d.full" % (prefix, n), addr)
        if addr:
            hdf.setValue("%s.%d.addr" % (prefix, n), addr)
        n = n + 1
    hdf.setValue(prefix, str(n))

  def export_message (self, prefix, hdf, m = None, as_text = 0, attach_str = ""):
    self._charset = None
    if m is None: m = self.message
    hdf.setValue ("%s.charset" % prefix, neo_cgi.htmlEscape(self.charset(m)))
    h_date = self.decode_header(m, 'date', as_utf8 = 0)
    if h_date:
      tup = date.parsedate_tz(h_date)
      if tup:
        try:
          t = date.mktime_tz(tup)
          hdf.setValue("%s.date_t" % prefix, str(t))
          neo_cgi.exportDate(hdf, "%s.h_date" % prefix, self._tz, t)
        except ValueError:
          log("Bad Date: %s" % repr(tup))
          pass
        except OverflowError:
          log("Bad Date: %s" % repr(tup))
          pass
      hdf.setValue ("%s.h_date" % prefix, neo_cgi.htmlEscape(self.decode_header(m, 'date', as_utf8 = 1)))
    hdf.setValue ("%s.h_from" % prefix, htmlhelp.emailEscape(maskAddr(self.decode_header(m, 'from', as_utf8 = 1))))
    hdf.setValue ("%s.h_to" % prefix, htmlhelp.emailEscape(maskAddr(self.decode_header(m, 'to', as_utf8 = 1))))
    hdf.setValue ("%s.h_cc" % prefix, htmlhelp.emailEscape(maskAddr(self.decode_header(m, 'cc', as_utf8 = 1))))
    hdf.setValue ("%s.h_subject" % prefix, neo_cgi.htmlEscape(self.decode_header(m, 'subject', as_utf8 = 1)))
    self.export_address_header("%s.addr.from" % prefix, hdf, m, 'from')
    self.export_address_header("%s.addr.to" % prefix, hdf, m, 'to')
    self.export_address_header("%s.addr.cc" % prefix, hdf, m, 'cc')
    self._urls = {}
    if attach_str: self.embedded_parts(m, attach_str, self._urls)
    if as_text:
      body = self.part_as_text (m)
      body = re.sub("\s([^\s@]+)@([^\s@]+\.[^\s@]+)","\\1@...",body)

      hdf.setValue("%s.textbody" % prefix,neo_cgi.htmlEscape(body))
    else:
      self.export_part (m, prefix, hdf)


  def as_text (self):
    self._charset = None
    m = self.message
    return self.part_as_text (m)
  
  def part_as_text (self, m):
    if m.ismultipart():
      if m.getsubtype("mixed") == "alternative":
        sub = []
        for sm in m.get_payload():
          st = sm.gettype("text/plain")
          if st == "text/plain":
            sub.insert(0, sm)
          else:
            sub.append(sm)
        if sub:
          return self.decode_part(sub[0], as_utf8 = 1)
      else:
        num = 0
        output = []
        for sm in m.get_payload():
          output.append(self.part_as_text(sm))
          num = num+1
        return string.join(output, '\n')
    else:
      ct = m.getmaintype("text")
      st = m.getsubtype("plain")
      if ct == "text":
        if st == "html":
          return convert_html_to_text(self.decode_part(m), 'utf-8')
        return self.decode_part(m, as_utf8 = 1)
      else:
        return ""

def decode_header (val, as_utf8 = 0):
  output, charset = MimeQPEnc.rfc2047_decode (val)
  if charset and as_utf8: return to_utf8(output, charset)
  return output

UNKNOWN_CHARSETS = {}

def to_utf8 (s, charset):
  charset = string.lower(charset)
  charset = string.replace(charset, '"', '')
  charset = string.strip(charset)
  x = string.find(charset, ';')
  if x != -1:
    charset = charset[:x]
  if not charset:
    charset = "iso-8859-1"
  if charset[:8] == "windows-":
    charset = "cp" + charset[8:]
  if charset[:4] == "win-":
    charset = "cp" + charset[4:]
  if charset[:3] == 'cp-':
    charset = "cp" + charset[3:]
  if charset == "us-ascii":
    charset = "ascii"
  # I've also seen kor-ascii... I don't know what that is, though
  if charset in ["ksc5601", 'ks_c_5601-1987', 'ms949', '5601']:
    charset = "cp949"
  elif charset == 'euc_kr':
    charset = 'euc-kr'
  elif charset == 'koi8r':
    charset = 'koi8-r'
  elif charset in ["gb2312", "gb2312_charset", "chinese-gb2312"]:
    charset = "gbk"
  elif charset == "iso-8859-11":  # libiconv doesn't have this yet
    charset = "TIS-620"
  elif charset == "unicode-1-1-utf-7":
    charset = "utf-7"
  elif charset == "unicode-1-1-utf-8":
    charset = "utf-8"
  elif charset in ["default", 'unknown', 'unknown-8bit', 'x-user-defined', '_charset', 'default_charset', 'x-unknown', '8859_1', 'ansi', 'iso08859-1', '8859-1', 'us-asci', 'asci', 'standard', 'ansi_charset', 'iso-8859-1-windows-3.1-latin-1']: # idiots
    charset = "iso-8859-1"
  elif charset in ["chinesebig5_charset", "chinesebig5"]:
    charset = "big5"
  elif charset == 'koi8-r.xlt':
    charset = 'koi8-r'
  elif charset == "x-sjis":
    charset = 'sjis'
  elif charset == 'iso-8859-8-i':
    charset = 'iso-8859-8'
  elif charset == 'dos-862':
    charset = 'cp862'
  elif charset == 'x-roman8':
    charset = 'hp-roman8'
  elif charset == "x-mac-cyrillic":
    charset = 'maccyrillic'
  elif charset.find('euc-kr') != -1:
    charset = 'euc-kr'
  elif charset.find('big5') != -1:
    charset = 'big5'
  elif charset != 'iso-8859-11' and charset.find('iso-8859-1') != -1:
    charset = 'iso-8859-1'
  elif charset.find('gb2312') != -1:
    charset = 'gb2312'
  elif charset.find('iso-2022-jp') != -1:
    charset = 'iso-2022-jp'

  if not charset:
    charset = 'iso-8859-1'

  if charset == 'utf-8':
    return s

  # use the kconv library, it works better with japanese...
  if kconv is not None and charset in ['iso-2022-jp', 'sjis', 'euc-jp']:
    kc = kconv.Kconv(kconv.UTF8)
    try:
        return kc.convert(s)
    except:
        import handle_error
        handle_error.handleException("Unable to kconv decode [%s]" % charset)

  try:
    return unicode(s, charset, 'ignore').encode('utf-8')
  except UnicodeError, reason:
    if string.find(str(reason), "ASCII decoding error") != -1:
      if string.find(s, chr(0x91)) != -1: charset = 'cp1252'
      else: charset = 'iso-8859-1'
      try:
        return unicode(s, charset).encode('utf-8')
      except UnicodeError, reason:
        pass
    import handle_error
    handle_error.handleException("Unable to decode [%s] %s" % \
                                 (charset,string.replace(string.replace(s[500:],"\n","\\n"),"\r","\\r")), dump=0)
  except LookupError:
    global UNKNOWN_CHARSETS
    if not UNKNOWN_CHARSETS.has_key(charset):
        import handle_error
        handle_error.handleException("Unable to find decode charset '%s'" % charset)
    UNKNOWN_CHARSETS[charset] = 1
  return s

USE_LINKS = 0

def convert_html_to_text (html_s, charset):
  if USE_LINKS and os.path.isfile('/usr/local/bin/links'):
    temp_file = os.tmpnam()
    try:
      fp = open(temp_file, 'w')
      fp.write(html_s)
      fp.close()
      fp = os.popen ('export HOME=/home/neo; /usr/local/bin/links -assume-codepage utf-8 -dump %s' % temp_file)
      out = fp.read()
      fp.close()
      os.unlink(temp_file)
      return out
    except:
      import handle_error
      handle_error.handleException("Unable to launch links")
      try:
        os.unlink(temp_file)
      except:
        pass
  
  from html2text import html2text
  out = html2text (html_s, use_ansi = 0, is_latin1 = (charset == 'iso-8859-1'))
  return out

VERSION = "0.1"

class NeoGenerator (Generator.Generator):
  def encode_header (self, header, charset):
    if count_nonascii (header, check=1):
      if charset == 'us-ascii': charset = 'iso-8859-1' 
      header = MimeQPEnc.encode_rfc2047 (header, charset = charset)
    return header

  def _writeheaders(self, msg, fp, suppress):
    charset = msg.getparam('charset', 'us-ascii')
    for h, v in msg.items():
      if h.lower() == 'mime-version' and suppress:
        continue
      elif h.lower() in ["from", "to", "cc"]:
        addrs = rfc822.AddressList(v)
        o_addrs = rfc822.AddressList(None)
        for (name, addr) in addrs:
            name = self.encode_header(name, charset)
            if addr:
                o_addrs.addresslist.append((name, addr))
        print >> fp, h + ': ', o_addrs
      elif h.lower() == 'subject':
        print >> fp, h + ':', self.encode_header(v, charset)
      else:
        print >> fp, h + ':', v


def count_nonascii (str, check = 0):
  count = 0  
  for x in range (len (str)):    
    o = ord(str[x])
    if o != 9 and o != 10 and o != 13 and (o > 127 or o < 32):
      count = count + 1
      if check:
        return count
  return count
