#!/neo/opt/bin/python

import string, re, time, rfc822
from log import log

try:
    import kconv
except:
    kconv = None

LANG_MAPPING = {'en': 'iso-8859-1',
                'es': 'iso-8859-1', 
                'de': 'iso-8859-1', 
                'fr': 'iso-8859-1', 
                'it': 'iso-8859-1', 
                'pt': 'iso-8859-1', 
                'br': 'iso-8859-1', 
                'nl': 'iso-8859-1', 
                'jp': 'iso-2022-jp', 
                'cn': 'gb2312', 
                'b5': 'big5', 
                'kr': 'euc-kr',
                'ru': 'koi8-r',
               }

CHARSET_EQUIV_MAPPING = {
                       # latin 1 (western european)
                       'iso-8859-1' : 'iso-8859-1',
                       'cp-1252' : 'iso-8859-1',
                       'cp1252' : 'iso-8859-1',
                       'windows-1252' : 'iso-8859-1',
                       # central european
                       'iso-8859-2' : 'iso-8859-2',
                       'windows-1250' : 'iso-8859-2',
                       'cp-1250' : 'iso-8859-2',
                       'cp1250' : 'iso-8859-2',
                       # greek
                       'iso-8859-7' : 'iso-8859-7',
                       'windows-1253' : 'iso-8859-7',
                       'cp-1253' : 'iso-8859-7',
                       'cp1253' : 'iso-8859-7',
                       # japanese
                       'iso-2022-jp' : 'iso-2022-jp',
                       'iso-2022-jp-1' : 'iso-2022-jp',
                       'iso-2022-jp-2' : 'iso-2022-jp',
                       'euc-jp' : 'iso-2022-jp',
                       'sjis' : 'iso-2022-jp',
                       'shift-jis' : 'iso-2022-jp',
                       'cp932' : 'iso-2022-jp',
                       'jis' : 'iso-2022-jp',
                       # korean
                       'iso-2022-kr' : 'euc-kr',
                       'johab' : 'euc-kr',
                       'euc-kr' : 'euc-kr',
                       'cp949' : 'euc-kr',
                       'cp-949' : 'euc-kr',
                       'ksc5601' : 'euc-kr',
                       'ks_c_5601-1987' : 'euc-kr',
                       # cyrillic
                       'koi8-r' : 'koi8-r',
                       'iso-8859-5' : 'koi8-r',
                       'cp-866' : 'koi8-r',
                       'cp866' : 'koi8-r',
                       'cp-1251' : 'koi8-r',
                       'windows-1251' : 'koi8-r',
                       # taiwan traditional chinese
                       'big5' : 'big5',
                       'euc-tw' : 'big5',
                       # china simple chinese
                       'gb2312' : 'gb2312',
                       'gbk' : 'gb2312',
                       }

def common_charset (charset1, charset2, lang=None):
    charset1 = string.lower(charset1)
    charset2 = string.lower(charset2)
    equiv_charset1 = CHARSET_EQUIV_MAPPING.get(charset1, charset1) 
    equiv_charset2 = CHARSET_EQUIV_MAPPING.get(charset2, charset2) 
    if equiv_charset1 == equiv_charset2:
        return equiv_charset1
    if charset1 == charset2: return charset1
    # in most cases, us-ascii is a subset of other charsets
    if charset1 == 'us-ascii': return charset2
    if charset2 == 'us-ascii': return charset1
    # in most cases, if the lang is english, iso-8859-1 equiv to us-ascii
    if lang == 'en':
        if charset1 == 'iso-8859-1': return charset2
        if charset2 == 'iso-8859-1': return charset1
    return 'utf-8'

PUNCT_MAP = [
    ("HYPHEN", chr(0xe2) + chr(0x80) + chr(0x90), "-"),
    ("NBHYPHEN", chr(0xe2) + chr(0x80) + chr(0x91), "-"),
    ("FIGUREDASH", chr(0xe2) + chr(0x80) + chr(0x92), "-"),
    ("ENDASH", chr(0xe2) + chr(0x80) + chr(0x93), "-"),
    ("EMDASH", chr(0xe2) + chr(0x80) + chr(0x94), "-"),
    ("HORIZBAR", chr(0xe2) + chr(0x80) + chr(0x95), "--"),
    ("LEFT_S_QUOTE", chr(0xe2) + chr(0x80) + chr(0x98), "'"),
    ("RIGHT_S_QUOTE", chr(0xe2) + chr(0x80) + chr(0x99), "'"),
    ("LEFT_S_LQUOTE", chr(0xe2) + chr(0x80) + chr(0x9A), ","),
    ("LEFT_S_RQUOTE", chr(0xe2) + chr(0x80) + chr(0x9B), "'"),
    ("LEFT_D_QUOTE", chr(0xe2) + chr(0x80) + chr(0x9C), '"'),
    ("RIGHT_D_QUOTE", chr(0xe2) + chr(0x80) + chr(0x9D), '"'),
    ("LEFT_D_LQUOTE", chr(0xe2) + chr(0x80) + chr(0x9E), ',,'),
    ("LEFT_D_RQUOTE", chr(0xe2) + chr(0x80) + chr(0x9F), '"'),
    ("BULLET", chr(0xe2) + chr(0x80) + chr(0xa2), chr(0xc2) + chr(0xb7)), # middot
    ("ONEDOT", chr(0xe2) + chr(0x80) + chr(0xa4), "."),
    ("TWODOT", chr(0xe2) + chr(0x80) + chr(0xa5), ".."),
    ("TRIDOT", chr(0xe2) + chr(0x80) + chr(0xa6), "..."),
    ("HYPHENPOINT", chr(0xe2) + chr(0x80) + chr(0xa7), chr(0xc2) + chr(0xb7)),
    ("REPLACE", chr(0xef) + chr(0xbf) + chr(0xbd), "?"),
    ("NBSP", chr(0xc2) + chr(0xa0), " "),
    ("IDSP", chr(0xe3) + chr(0x80) + chr(0x80), " "), # CJK space
    ]

def downgrade_utf8 (data):
    global PUNCT_MAP
    for (name, u8, asc) in PUNCT_MAP:
        data = data.replace(u8, asc)
    return data

def convert_from_utf8 (data, charset):
    if charset == 'utf8': return data 
    data = downgrade_utf8(data)
    if kconv is not None and charset == 'iso-2022-jp':
        kc = kconv.Kconv(kconv.JIS, kconv.UTF8)
        return kc.convert(data)
    return unicode(data, 'utf-8').encode(charset)

def return_first_nonascii (str):
  for x in range (len (str)):    
    if ord(str[x]) > 127 or ord(str[x]) < 32:
      return str[x]
  return ""

def charset_for_lang (lang):
  try:
    return LANG_MAPPING[lang]
  except:
    return 'utf-8'

def check_valid_email(email, check_domain=1):
    email = email.strip()
    al = rfc822.AddressList(email)
    if len(al) != 1: return 0
    if al[0][1] != email: return 0
    if check_domain:
        x = email.find('@')
        if x == -1: return 0
        if email[x:].find('.') == -1: return 0
    return 1

def get_sec_offset (timezone):
  if timezone:
    import Zone
    zone = Zone.Zone(timezone)
    (sec_offset, daylight, short) = zone.info()
    return sec_offset
  return 0

def date_header (time_t, timezone=None):
  sec_offset = get_sec_offset (timezone)
  tup = time.gmtime(time_t + sec_offset)
  datestr = time.strftime("%a, %d %b %Y %H:%M:%S", tup)
  if sec_offset <= 0: sign = '-'
  else: sign = '+'
  return "%s %s%02d00" % (datestr, sign, abs(sec_offset / 3600))

def strip_trak_tag (a_subject):
    tag_re = re.compile("(.*)\[([a-zA-Z]?)#([0-9]+)\](.*)")
    match = tag_re.match(a_subject)
    while match:
        a_subject = match.group(1) + match.group(4)
        match = tag_re.match(a_subject)
    return string.strip(a_subject)

def strip_re(subject_string):
    re_re = re.compile("((re(\\[[0-9]+\\])*|aw):[ \\t]*)(.*)", re.IGNORECASE)
    match = re_re.match(subject_string)
    while match:
        subject_string = match.group(4)
        match = re_re.match(subject_string)

    # strip kana-style subject tag headers
    subject_string = re.sub(" \(KMM[0-9A-Z]+KM\)","",subject_string)

    return string.strip(subject_string)

_COUNT = 0
_MSGID_RE = None
_MSGID_RE2 = None

def decompose_msgid (msgid):
    global _MSGID_RE, _MSGID_RE2
    if _MSGID_RE2 == None:
      _MSGID_RE2 = re.compile("([a-zA-Z]?)#(\w+)\.(\w+)\.(\w+)\.(\w+)\.(\w+)@")
    m = _MSGID_RE2.search(msgid)
    if m:
        r_type = m.group(1)
        orgnum = int(m.group(2), 16)
        ticket_id = int(m.group(3), 16)
        marker = "%s#%x.%x" % (r_type, orgnum, ticket_id)
        check = "%x" % hash(marker)
        if check == m.group(4):
            return r_type, orgnum, ticket_id
    if _MSGID_RE == None:
      _MSGID_RE = re.compile("([a-zA-Z]?)#(\w+)\.(\w+)\.(\w+)\.(\w+)@")
    m = _MSGID_RE.search(msgid)
    if m:
        r_type = m.group(1)
        ticket_id = int(m.group(2), 16)
        marker = "%s#%x" % (r_type, ticket_id)
        check = "%x" % hash(marker)
        if check == m.group(3):
            return r_type, -1, ticket_id
    return "", -1, None

def compose_msgid (domain, orgnum, ticket_id, ticket_type_tag = ""):
    global _COUNT
    _COUNT = _COUNT + 1
    marker = "%s#%x.%x" % (ticket_type_tag, orgnum, ticket_id)
    check = "%x" % hash(marker)
    return "<%s.%s.%x.%x@%s>" % (marker, check, int(time.time()), _COUNT, domain)
  
    
# We now have the trak_tag first because outlook will split it 
# on long subjects
def compose_subject(a_subject,ticket_id,ticket_type_tag = "",add_re=1):
    trak_tag = "[%s#%d]" % (ticket_type_tag, long(ticket_id))
    a_subject = strip_trak_tag(a_subject)
    if add_re:
        a_subject = strip_re(a_subject)
        a_subject = "Re: %s %s" % (trak_tag, a_subject)
    else:
        a_subject = "%s %s" % (trak_tag, a_subject)

    return a_subject

def word_truncate(line,length, maxwordsize=20):
    if len(line) < length:
        return line

    for i in range(maxwordsize):
        pos = length-i
        if pos > 0:
            if line[pos] == " ":
                return line[:pos]

    return line[:length]

def wrapwords(a_string_block,cols=74):
    new_string_lines = []
    WHITESPACE = ('\n',' ','\t','\r')

    pos = 0
    blocklen = len(a_string_block)

    while pos + cols < blocklen:
        newline_pos = string.find(a_string_block[pos:pos+cols],"\n")
        if newline_pos == -1:
            line_end = pos + cols
            while a_string_block[line_end] not in WHITESPACE and line_end > pos:
                line_end = line_end - 1

            if line_end != pos:
                new_string_lines.append(a_string_block[pos:line_end])
                pos = line_end + 1
            else:
                line_end = pos + cols
                while (line_end+1) < blocklen and a_string_block[line_end] not in WHITESPACE :
                    line_end = line_end + 1

                new_string_lines.append(a_string_block[pos:line_end])
                pos = line_end
                if a_string_block[pos] in WHITESPACE:
                    pos = pos + 1
                
        else:
            line_end = (pos + newline_pos)
            if line_end == pos:
                new_string_lines.append("")
            else:
                new_string_lines.append(a_string_block[pos:line_end])
            pos = line_end + 1

    new_string_lines.append(a_string_block[pos:])

    return string.join(new_string_lines,"\n")

def strip_re(subject_string, subj_prefix = None):
    if subj_prefix:
        subject_string = subject_string.replace(subj_prefix, '')
    subject_string = re.sub("\s+", " ", subject_string)
    subject_string = string.strip(subject_string)
    re_re = re.compile(" *re: (.*)", re.IGNORECASE)
    match = re_re.match(subject_string)
    while match:
        subject_string = match.group(1)
        match = re_re.match(subject_string)

    return string.strip(subject_string)

def strip_tag(subject_string):
    return re.sub("^\[[a-zA-Z\- ]+\] (.*)","\\1",subject_string)

def reduce_subject(subject_string, subj_prefix = None):
    if subj_prefix:
        subject_string = subject_string.replace(subj_prefix, '')
    subject_string = re.sub("\s+", "", subject_string)
    subject_string = string.strip(subject_string)
    re_re = re.compile("(re([\\[0-9\\]+])*|aw):[ \t]*(.*)", re.IGNORECASE)
    match = re_re.match(subject_string)
    while match:
        subject_string = match.group(3)
        match = re_re.match(subject_string)

    return string.strip(subject_string)

class RenderDataRE:
    def __init__(self,default_renderer=None):
        self._default_renderer = default_renderer
        self._re_render_list = []

    def addRenderer(self,regex,renderer):
        self._re_render_list.append( (regex,renderer) )

    def renderString(self,str):
        # find all the regexs and split the string apart into
        # typed pieces
        pieces = [ (-1,str) ]

        # first cut apart the data by type...
        render_index = 0
        for a_re,renderer in self._re_render_list:
            newpieces = []
            for dtype,data in pieces:
                m = re.search(a_re,data)
                while m:
                    st = m.start(0)
                    end = m.end(0)
                    # log("Matched: '%s' in '%s'" % (a_re,data))
                    
                    if st:
                        newpieces.append( (dtype,data[:st]) )
                    newpieces.append( (render_index,data[st:end]) )

                    log("  ---: %s" % data[st:end])

                    if end < len(data):
                        data = data[end:]
                        m = re.search(a_re,data)
                    else:
                        data = ""
                        m = None

                if data:
                    newpieces.append( (dtype,data) )
            pieces = newpieces
            render_index = render_index + 1

        outdata = []
        # second, reassemble the data
        for dtype,data in pieces:            
            if dtype == -1:
                if self._default_renderer:
                    outdata.append( self._default_renderer(data) )
                else:
                    outdata.append(data)
            else:
                repat,renderer = self._re_render_list[dtype]
                outpiece = re.sub(repat,renderer,data)
                outdata.append(outpiece)

        # third return the joined string
        return string.join(outdata,'')


def reply_quote_text(text,quote_char = ">"):
    lines = string.split(string.strip(text),"\n")
    lines = map(lambda line: quote_char + " " + line, lines)
    return string.join(lines,"\n")

if __name__ == "__main__":
    TEST_STRING = "foo bar foo bar foo bar"

    TEST_STRING2 = "\n\n\n\n\n\n\n\n\n\n\n"

    print "IN:  " + repr(TEST_STRING)
    print "OUT: " + repr(wrapwords(TEST_STRING,cols=2))
    
    print ""
    print "IN:  " + repr(TEST_STRING2)
    print "OUT: " + repr(wrapwords(TEST_STRING2,cols=2))


