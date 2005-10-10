
# 
# snippet.py
#
# engine for doing search result snippets
#
# import search_help
# snipper = search_help.Snippet()
# snippet = snipper.snippet(query,data)
#
# 04-17-02 - written by Brandon Long for discuss/archive
# 12-12-02 - adapted by Brandon Long for Trakken
# 03-08-03 - improved by David Jeske
#

import re, string
from log import log
import neo_cgi, neo_rtv
from wordwrap import WordWrap

class Snippet:
    def __init__ (self):
        pass

    def find_word_pos (self, word, data):
        WORD_DELIM = string.whitespace + string.punctuation
        loc = []
        lw = len(word)
        ld = len(data)
        r = 0
        while r < ld:
            i = string.find(data[r:], word)
            if i == -1: break
            r = r + i
            if r == 0 or data[r-1] in WORD_DELIM:
                if (r+lw == ld) or data[r+lw] in WORD_DELIM:
                    loc.append(r)
            r = r + 1
        return loc

    # grab a partial snippet 

    def partial(self, word, pos, data):
        lw = len(word)
        beg = pos
        end = pos+lw+1
        ld = len(data)
        pt = 0
        ascii_art = 0
        ws = 0
        portion = 0

        # extend the end
        while end < ld:
            if data[end] in ['_', '|']:
                ascii_art += 1
                if ascii_art > 4:
                    end = end - 4
                    break
                log("ascii art")
            elif data[end] in [',', '.', ')', '>', '?', '!']:
                pt = pt + 1
            elif data[end] in [' ', '\n'] and pt:
                portion = portion + 1
                if portion > 1:
                  end = end - 1
                  break
            elif data[end] in [' ', '\n']:
                ws = ws + 1
            else:
                pt = 0
                ws = 0
            if ws > 2: 
                portion = portion + 1
                if portion > 1:
                  end = end - ws
                  break
                ws = 0
            end = end + 1
        if end > ld: end = ld

        # backup the beginning
        ws = 0
        while beg > 0:
            if data[beg] in [' ', '\n']:
                ws = ws + 1
            elif data[beg] in ['.', ')', '>', '?', '!', '_', '|'] and ws:
                portion = portion + 1
                if portion > 1:
                  beg = beg + 1
                  break
            else:
                ws = 0
            if ws > 2: 
                portion = portion + 1
                if portion > 1:
                  beg = beg + ws
                  break
                ws = 0
            beg = beg - 1
        return beg, end

    def mark(self, phrase, loc, ofs):
        lp = len(phrase)
        i = len(loc) - 1
        while i >= 0:
            (pos, word) = loc[i]
            # if pos < ofs, the word is before the beginning, and
            # we're done because of the sorted order
            i = i - 1
            if pos < ofs: break
            if pos > ofs+lp: continue
            ld = len(word)
            phrase = phrase[:pos-ofs] + '\002' + phrase[pos-ofs:pos-ofs+ld] + '\003' + phrase[pos-ofs+ld:]
        return phrase

    def snippet(self, query, data):
        # --  sanitize data
        # - remove divider lines and spurious punctuation - jeske
        # - remove repeated whitespace to help partial()
        oldlen = len(data)
        data = re.sub("\s([-_*=+-]+\s)*\s*"," ",data)
        newlen = len(data)
        # log("sanitize removed: %d" % (oldlen-newlen))

        # find query parts in data
        qwords = neo_rtv.parse(query)
        # dwords = neo_rtv.parse(data)
        ldata = string.lower(data)
        qloc = []
        for word in qwords:
            loc = self.find_word_pos(word, ldata)
            # this really shouldn't happen... but maybe in some weird 
            # parsing cases, particularly since python's string.lower isn't
            # as smart as retrieves
            if len(loc) == 0: continue
            for pos in loc:
              qloc.append((pos, word))
        qloc.sort()

        # start assembling results
        out = []
        r = 0
        total = 0
        i = 0
        if len(qloc) == 0:
            (beg, end) = self.partial("", 0, data)
            out.append(data[beg:end])
        else:
            while i < len(qloc) and total < 200:
                (pos, word) = qloc[i]
                i = i + 1
                if pos < r: continue
                (beg, end) = self.partial(word, pos, data)
                if beg < r:
                    out[-1] = out[-1] + self.mark(data[r:end], qloc, r)
                    total = total + (end-r)
                else:
                    out.append(self.mark(data[beg:end], qloc, beg))
                    total = total + (end-beg)
                r = end
        snip = string.join(out, '... ')
        snip = string.replace(snip, '\n', ' ')
        snip = WordWrap(snip, cols=80)
        # this isn't necessary, they are stored already escaped
        snip = neo_cgi.htmlEscape(snip)
        lines = string.split(snip, '\n')
        snip = string.join(lines[:3], '\n')

        # why would we force newlines into the snippet? - jeske
        # snip = string.replace(snip, '\n', '<BR>')

        snip = string.replace(snip, '\002', '<B>')
        snip = string.replace(snip, '\003', '</B>')
        return snip
