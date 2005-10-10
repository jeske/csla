
import neo_cgi
import string
import re

from log import *

import msgutil

# msgrender.py
#
#
# plain text to html message rendering code


def BASIC_renderPlainTextToHtml(raw_body):
    raw_body = fixbody(string.strip(raw_body))
    body = neo_cgi.text2html(string.strip(raw_body))
    return body


def countSymbols(a_line):
    count = 0
    for a_char in a_line:
        if a_char in "<>{}():;-=+_&%#@![]$/\\":
            count = count + 1

    return count

def nonSymbolCount(a_line):
    count = 0
    for a_char in a_line:
        if not a_char in "<>{}():;-=+_&%#@![]$/\\":
            count = count + 1

    return count
    

def preformat(a_line):
    outline = ""
    nbsp_next = 0
    for a_char in a_line:
      if a_char == " ":
        if nbsp_next:
          nbsp_next = 0
          outline = outline + "&nbsp;"
        else:
          nbsp_next = 1
          outline = outline + " "
      elif a_char == "\t":
        nbsp_next = 0
        outline = outline + "&nbsp; &nbsp; &nbsp; &nbsp; "
      else:
        nbsp_next = 0
        outline = outline + a_char


    return outline

    # exerimental overhang wrap...
    # return '<div style="margin-left:10px;"><span style="margin-left:-10px;">' + outline + \
    #       '</span></div>'
            

def containsSymbols(a_line):
    symcnt = countSymbols(a_line)
    nonsymcnt = nonSymbolCount(a_line)
    if re.search("[\[\]/\\\$][^ ]+",a_line):
        return 1
    elif (symcnt > 4) or (symcnt+3 > nonsymcnt):
        return 1
    else:
        return 0

# must be global for the page!
hide_counter = 0

REPLACE_MARKER = "-BIGMARKER-"
    
class RenderResultInfo:
    def __init__(self):
        self.s = ''
        self.num_lines = 0
        self.num_quoted_lines = 0


class TextToHtmlRender:
    def __init__(self,debug=0):
        self._word_marks = {}
        self._cur_word_count = 0
        self._mark_insert_list = []
        self._hide_quote_at = {}
        self._debug = debug
        self.result = None # to hold number of quoted lines

    def renderSignatureBlock(self,qlines,hidden=1):
        global hide_counter
        
        if hidden:  
            display_mode = "none"
        else:
            display_mode = "block"
            

        output = []
        if hidden:
            output.append('<div style="cursor:pointer; cursor:hand;" onclick=toggleQDisplay("qhide_%s")>' % hide_counter)
            output.append('<font size=-2 color=#995500>&#167;</font></div>')
        output.append('<DIV ID=qhide_%s style="display:%s; margin-bottom:4px; color:#5050b0;">' % (hide_counter,display_mode))
        result = self._renderPlainTextToHtml(string.join(qlines,"\n"),hide_quoted=0)
        output.append(result.s)
        output.append("</div>")

        hide_counter = hide_counter + 1

        return string.join(output," ")
        

    def renderQuoteBlock(self,qlines,hidden=1):
        global hide_counter
        
        if hidden:  
            display_mode = "none"
        else:
            display_mode = "block"

        output = []
        if hidden:
            output.append('<div style="cursor:pointer; cursor:hand;" onclick=toggleQDisplay("qhide_%s")>' % hide_counter)
            output.append('&nbsp;&nbsp;<font size=-2 color=#995500>--&nbsp;Quoted text hidden. Click to expand&nbsp;--</font></div>')
        output.append('<DIV ID=qhide_%s style="display:%s; margin-bottom:4px; color:#5050b0;">' % (hide_counter,display_mode))
        result = self._renderPlainTextToHtml(string.join(qlines,"\n"),hide_quoted=0)
        output.append(result.s)
        output.append("</div>")

        hide_counter = hide_counter + 1

        return string.join(output," ")

    def addWordMarkAt(self,mark_id,word_pos):
        try:
            curmarks = self._word_marks[word_pos]
        except KeyError:
            curmarks = []
            self._word_marks[word_pos] = curmarks

        curmarks.append(mark_id)

    def hideQuoteAtWord(self,word_pos):
        self._hide_quote_at[word_pos] = 1

    def renderPlainTextToHtml(self,raw_body,hide_quoted=1):
        result = self._renderPlainTextToHtml(raw_body,hide_quoted=hide_quoted)
        log("result.num_lines: %d result.num_quoted_lines: %d" % (result.num_lines, result.num_quoted_lines))
        real_output = result.s 
        self.result = result # this is a hack to export quoted line number stats, it might not be a good solution

        mark_insert_list = self._mark_insert_list
        
        log("reprocessing marks --------- %s " % len(mark_insert_list))
        newoutparts = []

        for a_part in string.split(real_output,REPLACE_MARKER):
          newoutparts.append(a_part)
          
          if mark_insert_list:
            newoutparts.append(mark_insert_list[0])
            log("inserting mark: %s" % mark_insert_list[0])
            mark_insert_list = mark_insert_list[1:]
          else:
            log("no marks left!!")


        return string.join(newoutparts,"")
        
    def _renderPlainTextToHtml(self,raw_body, hide_quoted=1):
        # log("render: " + raw_body[:100])
        result = RenderResultInfo()

        raw_body = fixbody(string.strip(raw_body))

        lines = string.split(raw_body,"\n")
        result.num_lines = len(lines)

        def urlsub(match):
            url_text = match.group(1)
            if len(url_text) > 60:
                url_text = url_text[:60] + "..."
            return '<a class=newlink target=_blank href="%s">%s</a>' % (match.group(1), url_text)
        def news_urlsub(match):
            return '[<a class=newlink target=_blank href="http://groups.google.com/groups?as_umsgid=%s">msg</a>]' % neo_cgi.urlEscape(match.group(1))

        def chopword(match):
            outdata = []
            indata = match.group(0)
            while len(indata) > 80:
                outdata.append(indata[:80])
                indata = indata[80:]
            outdata.append(indata)
            return string.join(outdata," ")
            

        line_render = msgutil.RenderDataRE(default_renderer=neo_cgi.htmlEscape)
        line_render.addRenderer("([a-z]{3,10}://[[a-zA-Z0-9.]+[^ \t\n]*[^.,> ])",urlsub)
        # line_render.addRenderer("([-_*/])\\1{2,}","\\1")
        # line_render.addRenderer("[^\s]{80,}",chopword)

        line_render.addRenderer("([<\s][a-zA-Z0-9-_.+=]+)(@[a-zA-Z0-9-_.])[a-zA-Z0-9-_.]+([>\s])",
                              lambda m: neo_cgi.htmlEscape(m.group(1) + m.group(2) + "..." + m.group(3)))
        line_render.addRenderer("news:([^/][^ ]+@[0-9a-zA-Z-_.]+)",
                                news_urlsub)


        output = []
        quoted_text = []
        signature_text = []
        quoted_text_word_start = 0
        ws_lines = 0
        eat_rest = 0
        eat_rest_signature = 0
        in_paragraph = 0

        for a_line in lines:
            # this regex was hanging! - jeske
            # I think this was the input: "http://groups.yahoo.com/group/tuna/"
            # workaround terrible IE wrapping bug
            # if re.search("/(([^ ]+)){30,}",a_line):
            #     a_line = re.sub("/([^ ]+) ","    /    \\1 ",a_line)

            if re.match("[-]+ Yahoo! Groups Sponsor [-~>]+",a_line):
                break

            if re.match("Yahoo! Groups Links",a_line):
                eat_rest = 1
                break

            if re.match("mythtv-users mailing list",a_line):
                eat_rest = 1
                break

            # need to do our word counting here!
            word_line = re.sub("[^a-zA-Z0-9 ]"," ",a_line)
            insert_shift = 0
            word_arr = generateWordPosArr(word_line)

            # keep track of where quoted regions start
            if not quoted_text:
                quoted_text_word_start = self._cur_word_count

            # do mark insertion            
            for word_pos in word_arr:
                if self._word_marks.has_key(self._cur_word_count):
                    wref_list = self._word_marks[self._cur_word_count]
                    a_line = a_line[:word_pos+insert_shift] + REPLACE_MARKER + a_line[word_pos+insert_shift:]
                    insert_shift = insert_shift + len(REPLACE_MARKER)

                    # we're going to come back and put it in later
                    if self._debug:
                        self._mark_insert_list.append(string.join(map(lambda wref: '<span id="qref_%s" class=mark>%s</span>' % (wref,wref),wref_list),''))
                    else:
                        self._mark_insert_list.append(string.join(map(lambda wref: '<span id="qref_%s" class=mark></span>' % (wref),wref_list),''))
                
                self._cur_word_count = self._cur_word_count + 1

            # log("handle: " + a_line)
            # a_line = string.strip(a_line)
            if hide_quoted:
                if re.match("^-- $",a_line):
                    eat_rest_signature = 1
                    continue

                # hack for mythtv mailing list
                if re.match("_______________________________________________",a_line):
                    eat_rest_signature = 1
                    continue
                
                if eat_rest_signature:
                    signature_text.append(a_line)
                    continue

                if eat_rest or re.match("^([A-Z]{2})?[}>|]+( .*)?",a_line):
                    # quoted text
                    quoted_text.append(a_line)
                    result.num_quoted_lines += 1
                    continue

                if re.match(" *-+ ?Original Message ?(Follows )?-+ *",a_line):
                    output.append(a_line)
                    eat_rest = 1
                    continue

            if not string.strip(a_line):
                ws_lines = ws_lines + 1
                continue

            if len(quoted_text):
                hidden = 0
                # log("checking for range %s,%s -- %s" % (quoted_text_word_start,self._cur_word_count,repr(self._hide_quote_at)))
                for i in range(quoted_text_word_start,self._cur_word_count):
                    if self._hide_quote_at.has_key(i):
                        hidden = 1

                if len(quoted_text) > 15:
                    hidden = 1
                    
                output.append(self.renderQuoteBlock(quoted_text,hidden=hidden))
                in_paragraph = 0
                ws_lines = 0
                quoted_text = []

            if ws_lines:
                ws_lines = 0
                output.append("<p>")
                in_paragraph = 0

 
            # when we're rendering a quoted block, this outputs the lines
            if re.match("^([A-Z]{2})?[}>|]+( .*)?",a_line):
                output.append(line_render.renderString(a_line) + "<br>")
                in_paragraph = 0
                continue

            if re.search(" {5,}[^ ]+ {2,}",a_line):
                # whitespace formatted
                output.append(preformat(line_render.renderString(a_line)) +"<br>")
                in_paragraph = 0
                continue

            if re.match("^((\t+)|( {3,})).*",a_line):
                # indent
                output.append(preformat(line_render.renderString(a_line)) +"<br>")
                in_paragraph = 0
                continue

            if re.match(".*:\s*",a_line):
                # ends in a colon
                output.append(line_render.renderString(a_line) + "<br>")
                in_paragraph = 0
                continue


            if ( re.match("\s*[0-9a-z]+[).].*",a_line) or
                 re.match("\s*[-*=+]+ .*",a_line) ):
                # number/letter outlines, bullet lists
                if in_paragraph:
                    output.append("<br>")
                output.append(preformat(line_render.renderString(a_line)) +"<br>")
                in_paragraph = 0
                continue

            if re.match("[\t ]{3,}.*",a_line) or containsSymbols(a_line):
                output.append(preformat(line_render.renderString(a_line)) +"<br>")
                in_paragraph = 0
                continue

            if len(a_line) < 50:
                output.append(line_render.renderString(a_line) + "<br>")
                in_paragraph = 0
                continue

            # japansese non-wrap code from gaku...
            if 0:
                output.append(line_render.renderString(a_line) + "<br>")
                continue

            output.append(line_render.renderString(a_line))
            in_paragraph = 1

        if len(quoted_text):
            output.append(self.renderQuoteBlock(quoted_text))

        if len(signature_text):
            output.append(self.renderSignatureBlock(signature_text))
 
        result.s = string.join(output,"\n")
        return result


#########################
#
# fixbody(body_data)
#
# This function tries to fix bad things about email
# bodies. 
#
def fixbody(raw_body):
    log("-- fixbody")
    
    # FIX #1: reassemble broken URLs
    def fixurl(m):
        log("matched url: %s" % m.group(0))
        result = re.sub(" ?[\r\n]","",m.group(0))
        log("fixed url: %s" % result)
        return result

    raw_body = re.sub("[a-z]+://\S+"
                      "("
                      "("
                      "(/ ?\r?\n(?![a-z]{0,7}://))"
                      "|"
                      "( ?\r?\n/)"
                      "|"
                      "(- ?\r?\n)"
                      ")+"
                      "\S+)+"
                      "(?= ?\r?\n]>\\))",
                       fixurl,raw_body)

    raw_body = re.sub("[a-z]+://\S+( ?\r?\n(?![a-z]{0,7}://)\S+)+",fixurl,raw_body)

    # FIX #2: space pad URLs which are surrounded by (), <> or []
    raw_body = re.sub("([<([])([a-z]+://[^ ]+)([>)\\]])","\\1 \\2 \\3",raw_body)

    # FIX #3: remove Yahoo! Groups ad chunks

    # done with fixes
    return raw_body


# ----------------------------------------

import md5

class MatchTracker:
    def __init__(self,sequence_len,mid):
        self.start_loc = None  # source
        
        self.start_range = None
        self.end_range = None
        self.sequence_len = sequence_len
        self.mid = mid
        self.matches = []
    def handleMatch(self,x,source):
        # if we're not processing the next source word
        if (not self.end_range is None) and (self.end_range + 1 != x):
            self.makeMatchAndClear()
        # or if the source mid is not the same
        if (not self.start_loc is None) and source[0] != self.start_loc[0]:
            self.makeMatchAndClear()

        if not self.start_range:
            self.start_range = x
            self.start_loc = source
        self.end_range = x

    def makeMatchAndClear(self):
        # avoid overlapping matches shorter than self.sequence_len
        if (self.end_range-self.start_range) > self.sequence_len:
            self.matches.append( (self.start_loc,self.start_range,self.end_range+self.sequence_len) )
            log("  found match: (%s) %s-%s refs %s" % (self.mid,self.start_range,
                                                       self.end_range + self.sequence_len,
                                                       self.start_loc))
        self.start_loc = None
        self.start_range = None
        self.end_range = None

    def getMatches(self):
        if not self.start_loc is None:
            self.makeMatchAndClear()
        return self.matches


def generateWordPosArr(data):
    arr = []
    in_word = 0
    text_len = len(data)

    for x in range(text_len):
        ch = data[x]
        if in_word:
            if ch == " ":
                in_word = 0
        else:
            if ch != " ":
                arr.append(x)
                in_word = 1
    return arr
    

class Match:
  def __init__(self):
    self.source_mid = None
    self.source_start = None
    self.source_pct = None
    self.dest_mid = None
    self.dest_start = None
    self.dest_end = None
    
  def hdfExport(self,prefix,hdf):
    hdf.setValue(prefix + ".source_mid",str(self.source_mid))
    hdf.setValue(prefix + ".source_start",str(self.source_start))
    hdf.setValue(prefix + ".source_pct",str(self.source_pct))
    hdf.setValue(prefix + ".dest_mid",str(self.dest_mid))
    hdf.setValue(prefix + ".dest_start",str(self.dest_start))
    hdf.setValue(prefix + ".dest_end",str(self.dest_end))
    

class TextSourceMatcher:
    def __init__(self):
        self._map_dict = {}
        self._doc_word_count = {}
        self._doc_word_pos_arr = {}
        self._refsByDocId = {}
        self._refsOfDocId = {}

    def getLocForDoc_andWord_(self,mid,wordindex):
        return self._doc_word_pos_arr[mid][wordindex]

    def addAndMatchText(self,mid,text):
        mid = str(mid)
        PICK_COUNT = 6

        mt = MatchTracker(PICK_COUNT,mid)

        # eliminate confusing punctuation from our observation
        text = re.sub("[^a-zA-Z0-9 ]"," ",text)

        # we need to generate the word -> position map
        self._doc_word_pos_arr[mid] = generateWordPosArr(text)
        
        words = string.split(text)
        self._doc_word_count[mid] = len(words)
        
        for x in range(len(words)-PICK_COUNT):
            m = md5.new()
            for word in words[x:x+PICK_COUNT]:
                m.update(word)

            dig = m.digest()
            if self._map_dict.has_key(dig):
                # already seen!
                prevmatch = self._map_dict[dig]
                # avoid self-references
                if prevmatch[0] != mid:
                    mt.handleMatch(x,prevmatch)
            else:
                self._map_dict[dig] = (mid,x)

        matchreturn = []
        for source_loc,dest_start,dest_end in mt.getMatches():
            match_len = dest_end-dest_start
            src_mid, src_start = source_loc
            match_pct = (match_len*100)/self._doc_word_count[src_mid]

            log("match pct: %s" % match_pct)
            matchinfo = Match()
            matchinfo.source_mid = src_mid
            matchinfo.source_start = src_start
            matchinfo.source_pct = match_pct
            matchinfo.dest_mid = mid
            matchinfo.dest_start = dest_start
            matchinfo.dest_end = dest_end
            matchreturn.append( matchinfo )

            self._addRefForSource(matchinfo)

        self._refsByDocId[mid] = matchreturn

        return matchreturn

    def _addRefForSource(self,matchinfo):
        try:
            mlist = self._refsOfDocId[matchinfo.source_mid]
        except KeyError:
            mlist = []
            self._refsOfDocId[matchinfo.source_mid] = mlist
        mlist.append(matchinfo)

    def getRefsByDocId(self,mid):
        try:
            return self._refsByDocId[str(mid)]
        except KeyError:
            return []

    def getRefsOfDocId(self,mid):
        try:
            return self._refsOfDocId[str(mid)]
        except KeyError:
            return []
