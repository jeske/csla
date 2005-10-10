
import os, sys, string, re, time
import marshal

from TCS.bsddb import db

import neo_cgi, neo_util
import neo_rtv
import email_message
from mimelib import Message, Generator, Parser, date
from log import *
import rfc822

import search_help

eNoMessage = "eNoMessage"

class Message:
    def __init__ (self, ms):
        # v1 = [version, doc_id, thread_id, parent_id, next_id, child_id, offset, length, date (time_t), subject, author, email]
        meta = marshal.loads(ms)
        if meta[0] == 1:
            (version, self.doc_id, self.thread_id, self.parent_id, self.next_id, self.child_id, self.offset, self.length, self.date_t, self.subject, self.author, self.email) = meta
        else:
            raise "Unknown meta version"

        # This has to be set independently
        self.summary = None
        self.msg_data = None
        self.snippet = None

    def encode(self):
        meta = [1, self.doc_id, self.thread_id, self.parent_id, self.next_id, self.child_id, self.offset, self.length, self.date_t, self.subject, self.author, self.email]
        meta_s = marshal.dumps(meta)
        return meta_s
       
    def hdfExport(self, prefix, hdf, tz="US/Pacific", subj_prefix=None):
        hdf.setValue(prefix, "1")
        obj = hdf.getObj(prefix)
        obj.setValue("doc_id", str(self.doc_id))
        obj.setValue("thread_id", str(self.thread_id))
        obj.setValue("parent_id", str(self.parent_id))
        obj.setValue("next_id", str(self.next_id))
        obj.setValue("child_id", str(self.child_id))
        if self.date_t:
            neo_cgi.exportDate(obj, "date", tz, self.date_t)

        subject = self.subject
        if subj_prefix:
            subject = subject.replace(subj_prefix, '')
        obj.setValue("subject", neo_cgi.htmlEscape(subject))
        obj.setValue("subject_strip", neo_cgi.htmlEscape(strip_re(subject, subj_prefix=subj_prefix)))
        obj.setValue("subject_reduced", reduce_subject(subject, subj_prefix=subj_prefix))

        obj.setValue("author", neo_cgi.htmlEscape(self.author))
        obj.setValue("email", neo_cgi.htmlEscape(self.email))
        if self.summary is not None:
            obj.setValue("summary", neo_cgi.text2html(self.summary))
        if self.snippet is not None:
            obj.setValue("snippet", self.snippet)

class MessageIndex:
    # Maps message number to message meta information
    def __init__ (self, path, mode):
        dbf = db.DB()
        self._path = path
        path = "%s/archive/msgidx.db" % self._path
        if mode == 'w':
            dbf.open(path, db.DB_BTREE, db.DB_CREATE)
        else:
            dbf.open(path, db.DB_BTREE, db.DB_RDONLY)
        self._db = dbf

        self._arc = None
        self._arc_mode = None

    def openArchive(self, mode):
        if self._arc is None or self._arc_mode != mode:
            self._arc = open("%s/archive/archive" % self._path, mode)
            self._arc_mode = mode
        return self._arc

    def __del__ (self):
        self.close()

    def close(self):
        if self._db is not None:
            self._db.close()
            self._db = None

    def add(self, doc_id, msg_data, parent_id, thread_id, date_t, h_subj, author, email):
        arc = self.openArchive('a')
        offset = arc.tell()
        arc.write("--@@-- BEGIN --@@--\n%s\n==@@== END ==@@==\n" % msg_data)
        length = arc.tell() - offset

        parent_meta = None
        if thread_id == 0:
            parent_meta = self.get(parent_id)
            thread_id = parent_meta.thread_id

        # v1 = [version, doc_id, thread_id, parent_id, next_id, child_id, offset, length, date (time_t), subject, author, email]
        meta = [1, doc_id, thread_id, parent_id, 0, 0, offset, length, date_t, h_subj, author, email]
        meta_s = marshal.dumps(meta)
        self._db.put(str(doc_id), meta_s)

        if parent_meta is not None:
            if parent_meta.child_id == 0:
                parent_meta.child_id = doc_id
                self.save(parent_meta)
            else:
                child_meta = self.get(parent_meta.child_id)
                while child_meta.next_id:
                    child_meta = self.get(child_meta.next_id)

                child_meta.next_id = doc_id
                self.save(child_meta)

        return thread_id

    def save(self, msg_meta):
        meta_s = msg_meta.encode()
        self._db.put(str(msg_meta.doc_id), meta_s)

    def get(self, doc_id, full = 0):
        try:
            meta = Message(self._db.get(str(doc_id)))
        except db.error, reason:
            if reason[0] == -7:
                raise eNoMessage
            raise
        if full == 0: return meta
        arc = self.openArchive('r')
        arc.seek(meta.offset)
        msg_data = arc.read(meta.length)
        if msg_data[:20] == '--@@-- BEGIN --@@--\n' and \
           msg_data[-18:] == '==@@== END ==@@==\n':
            meta.msg_data = msg_data[20:-18]
        else:
            raise eNoMessage
        return meta

class ByMonth:
    def __init__ (self, path):
        self._path = path
        self._data = None
        self._modified = 0
        self.load()

    def load(self):
        # v1 = "year/month first_num count"
        self._data = {}
        path = "%s/archive/by_month" % self._path
        if not os.path.exists(path): return
        fp = open(path)
        header = fp.readline()
        if header != 'BY_MONTH_v1\n':
            raise "Unknown ByMonth Version"
        for line in fp.readlines():
            parts = line.split(' ')
            if len(parts) == 3:
                self._data[parts[0]] = (int(parts[1]), int(parts[2]))

    def get(self, month):
        month = month.replace('-', '/')
        (first_num, count) = self._data.get(month, (0, 0))
        return (first_num, count)

    def add(self, doc_id, date_t):
        tup = time.localtime(date_t)
        year = tup[0]
        mon = tup[1]
        date = '%s/%02d' % (year, mon)
        (first_num, count) = self._data.get(date, (0, 0))
        if first_num == 0 or doc_id < first_num:
            first_num = doc_id
        count = count + 1
        self._data[date] = (first_num, count)
        self._modified = 1

    def __del__ (self):
        self.save()

    def save (self):
        if self._modified:
            path = "%s/archive/by_month" % self._path
            fp = open(path + ".tmp", 'w')
            fp.write('BY_MONTH_v1\n')
            dates = self._data.keys()
            dates.sort()
            for date in dates:
                (first_num, count) = self._data[date]
                fp.write("%s %s %s\n" % (date, first_num, count))
            fp.close()
            os.rename(path + ".tmp", path)
            self._modified = 0

    def hdfExport(self, prefix, hdf, reverse=0):
        dates = self._data.keys()
        if not dates:
            # if there is no data...
            return
        dates.sort()
        first_date = dates[0]
        (first_year, month) = first_date.split('/')
        first_year = int(first_year)
        last_date = dates[-1]
        (last_year, month) = last_date.split('/')
        last_year = int(last_year)
        if reverse:
            year = last_year
            while year >= first_year:
                for mon in range(1,13):
                    (first_num, count) = self._data.get("%d/%02d" % (year, mon), (0,0))
                    hdf.setValue("%s.%s.%s.num" % (prefix, year, mon), str(first_num))
                    hdf.setValue("%s.%s.%s.count" % (prefix, year, mon), str(count))
                    hdf.setValue("%s.%s.%s.year" % (prefix, year, mon), str(year))
                    hdf.setValue("%s.%s.%s.mon" % (prefix, year, mon), "%02d" % mon)
                year -= 1
        else:
            year = first_year
            while year <= last_year:
                for mon in range(1,13):
                    (first_num, count) = self._data.get("%d/%02d" % (year, mon), (0,0))
                    hdf.setValue("%s.%s.%s.num" % (prefix, year, mon), str(first_num))
                    hdf.setValue("%s.%s.%s.count" % (prefix, year, mon), str(count))
                    hdf.setValue("%s.%s.%s.year" % (prefix, year, mon), str(year))
                    hdf.setValue("%s.%s.%s.mon" % (prefix, year, mon), "%02d" % mon)
                year += 1
        

class MessageSummary:
    # Maps message number to message summary
    def __init__ (self, path, mode):
        dbf = db.DB()
        self._path = path
        path = "%s/archive/summary.db" % self._path
        if mode == 'w':
            dbf.open(path, db.DB_BTREE, db.DB_CREATE)
        else:
            dbf.open(path, db.DB_BTREE, db.DB_RDONLY)
        self._db = dbf

    def __del__ (self):
        self.close()

    def close(self):
        if self._db is not None:
            self._db.close()
            self._db = None

    def add(self, doc_id, summary):
        self._db.put(str(doc_id), summary)

    def get(self, doc_id):
        try:
            return self._db.get(str(doc_id))
        except db.error, reason:
            if reason[0] == -7:
                return ""
            raise

class ThreadIndex:
    # Maps thread ids to message numbers
    def __init__ (self, path, mode):
        dbf = db.DB()
        self._path = path
        path = "%s/archive/threads.db" % self._path
        if mode == 'w':
            dbf.open(path, db.DB_BTREE, db.DB_CREATE)
        else:
            dbf.open(path, db.DB_BTREE, db.DB_RDONLY)
        self._db = dbf

    def __del__ (self):
        self.close()

    def close(self):
        if self._db is not None:
            self._db.close()
            self._db = None

    def add(self, thread_id, doc_id):
        doc_list = self.get(str(thread_id))
        doc_list.append(str(doc_id))
        dlist = string.join(doc_list, ',')
        self._db.put(str(thread_id), dlist)

    def get(self, thread_id):
        try:
            dlist = self._db.get(str(thread_id))
            dlist = string.split(dlist, ',')
            return dlist
        except db.error, reason:
            if reason[0] == -7:
                return []
            raise

class MessageIDIndex:
    # Maps message ids to message numbers
    def __init__ (self, path, mode):
        dbf = db.DB()
        self._path = path
        path = "%s/archive/msgids.db" % path
        if mode == 'w':
            dbf.open(path, db.DB_BTREE, db.DB_CREATE)
        else:
            dbf.open(path, db.DB_BTREE, db.DB_RDONLY)
        self._db = dbf

    def __del__ (self):
        self.close()

    def close(self):
        if self._db is not None:
            self._db.close()
            self._db = None

    def find(self, references):
        # technically, this message shouldn't be in the list...
        # ok, for now we'll just use the latest thread, which is the first
        # found (as the references are in latest first order)
        for ref in references:
            try:
                doc_id = self._db.get(ref)
                return int(doc_id)
            except db.error, reason:
                if reason[0] == -7: # DB_NOTFOUND
                    continue
                raise db.error, reason
        return 0

    def add(self, msg_id, doc_id):
        self._db.put(msg_id, str(doc_id))

class AuthorIndex:
    # Maps email address to name and posts by month
    def __init__ (self, path, mode):
        dbf = db.DB()
        self._path = path
        path = "%s/archive/authors.db" % self._path
        if mode == 'w':
            dbf.open(path, db.DB_BTREE, db.DB_CREATE)
        else:
            dbf.open(path, db.DB_BTREE, db.DB_RDONLY)
        self._db = dbf

    def __del__ (self):
        self.close()

    def close(self):
        if self._db is not None:
            self._db.close()
            self._db = None

    def add(self, author, email, date_t):
        if not email: return
        email = email.strip()
        tup = time.localtime(date_t)
        year = tup[0]
        mon = tup[1]
        date = '%s-%02d' % (year, mon)
        (junk, name, bymonth) = self.get(email)
        if not author:
            author = name
        total = bymonth.get('total', 0)
        total += 1
        bymonth['total'] = total
        count = bymonth.get(date, 0)
        count += 1
        bymonth[date] = count

        bym = string.join(map(lambda x: '%s:%d' % x, bymonth.items()))
        self._db.put(email.lower(), '%s%s%s' % (email, author, bym))

        # add to "totals" list
        data = self.get_top('total')
        if len(data) == 0:
            data.append((total, email))
            self.write_top('total', data)
        else:
            (min_total, junk) = data[-1]
            if len(data) < 50 or min_total <= total:
                data.append((total, email))
                self.write_top('total', data)

        # add to proper month
        data = self.get_top(date)
        if len(data) == 0:
            data.append((count, email))
            self.write_top(date, data)
        else:
            (min_count, junk) = data[-1]
            if len(data) < 50 or min_count <= count:
                data.append((count, email))
                self.write_top(date, data)

    def get(self, email):
        try:
            data = self._db.get(email.lower())
        except db.error, reason:
            if reason[0] == -7: # DB_NOTFOUND
                return email, "", {}
            log("Unable to fetch record for email: '%s'" % email)
            raise db.error, reason
        # v1 = "emailname^Ayear-mon:count year-mon:count total:count"
        (email, name, bym) = data.split('')
        mon_data = bym.split(' ')
        bymonth = {}
        for part in mon_data:
            (date, count) = part.split(':')
            bymonth[date] = int(count)

        return email, name, bymonth

    def get_top(self, date):
        path = "%s/archive/authors_%s.top" % (self._path, date)
        if not os.path.exists(path):
            return []

        fp = open(path)
        header = fp.readline()
        if header != 'TOP_AUTHOR_v1\n':
            raise "Unknown Top Author Version"
        data = []
        for line in fp.readlines():
            try:
                (email, count) = line.strip().split('')
                data.append((int(count), email))
            except ValueError:
                print "get_top: error parsing: %s" % line
                continue

        return data        

    def write_top(self, date, data):
        path = "%s/archive/authors_%s.top" % (self._path, date)
        fp = open(path + '.tmp', 'w')
        fp.write('TOP_AUTHOR_v1\n')
        data.sort()
        data.reverse()

        seen = {}
        n = 0
        for (count, email) in data:
            email = email.lower()
            if seen.has_key(email): continue
            seen[email] = 1
            fp.write("%s%s\n" % (email, count))
            n += 1
            if n >= 50: break
        fp.close()
        os.rename(path + '.tmp', path)

class SearchIndex:
    # Full text index of the messages
    def __init__ (self, path, mode):
        self._rtv = None
        self._path = path
        path = "%s/search" % self._path
        if mode == 'w':
            try:
                rtv = neo_rtv.Retrieve(path, 0)
            except neo_rtv.NeoError:
                rtv = neo_rtv.RetrieveCreate(path, ["DOCID_LENGTH 50", "COLLECTION_MAX_DOCS 40000"])
        else:
            rtv = neo_rtv.Retrieve(path, neo_rtv.NTR_OPEN_RO)
        self._rtv = rtv
        self._rtv_count = 0
    
    def __del__ (self):
        self.close()

    def close(self):
        if self._rtv is not None:
            self._rtv.docFlush()
            self._rtv = None

    def add(self, msg_num, msgobj, email):
        # Ok, time to index the actual message
        rm = email_message.RenderMessage(mimemsg=msgobj)
        self._rtv.docStart(str(msg_num))
        for hdr in ["to", "from", "cc", "subject", "x-mailer", "mailing-list", "reply-to"]:
            val = rm.decode_header(msgobj, hdr, "", as_utf8=1)
            if val: self._rtv.docParse(val)
        data = rm.as_text()
        self._rtv.docAddWord("AUTHOR:%s" % string.lower(email))
        self._rtv.docParse(data)

        self._rtv_count = self._rtv_count + 1
        #if self._rtv_count % 2000 == 0:
        #    rtv.docFlush()

    def search(self, query, attrs=[]):
        results = self._rtv.search(query, attrs)
        # results.reverse()
        return results

class MessageDB:
    def __init__ (self, path):
        self._path = path
        self._messageIndex = None
        self._messageIndex_mode = None
        self._byMonth = None
        self._messageSummary = None
        self._messageSummary_mode = None
        self._threadIndex = None
        self._threadIndex_mode = None
        self._messageIDIndex = None
        self._messageIDIndex_mode = None
        self._authorIndex = None
        self._authorIndex_mode = None
        self._searchIndex = None
        self._searchIndex_mode = None

        self.config = neo_util.HDF()
        self._config_file = "%s/archive/mdb.hdf" % self._path
        if not os.path.exists(self._path + '/archive'):
            os.makedirs(self._path + '/archive', 0777)
        if os.path.exists(self._config_file):
            self.config.readFile(self._config_file)
        self._config_dirty = 0

        self._parser = None

        try:
            if 0: db.appinit(path, db.DB_INIT_LOCK | db.DB_CREATE)
        except:
            raise "failure opening DB Env at: %s" % path


    def __del__ (self):
        self.flush()
        try:
            if 0: db.appexit()
        except:
            raise "Unable to appexit"

    def flush(self):
        if self._config_dirty:
            self.config.writeFile("%s/archive/mdb.hdf" % self._path)
            self._config_dirty = 0
        self._messageIndex = None
        self._messageIndex_mode = None
        self._byMonth = None
        self._messageSummary = None
        self._messageSummary_mode = None
        self._threadIndex = None
        self._threadIndex_mode = None
        self._messageIDIndex = None
        self._messageIDIndex_mode = None
        self._authorIndex = None
        self._authorIndex_mode = None
        self._searchIndex = None
        self._searchIndex_mode = None

    def openMessageIndex(self, mode):
        if self._messageIndex is None or self._messageIndex_mode != mode:
            self._messageIndex = MessageIndex(self._path, mode)
            self._messageIndex_mode = mode
        return self._messageIndex

    def openByMonth(self):
        if self._byMonth is None:   
            self._byMonth = ByMonth(self._path)
        return self._byMonth

    def openMessageSummary(self, mode):
        if self._messageSummary is None or self._messageSummary_mode != mode:
            self._messageSummary = MessageSummary(self._path, mode)
            self._messageSummary_mode = mode
        return self._messageSummary

    def openThreadIndex(self, mode):
        if self._threadIndex is None or self._threadIndex_mode != mode:
            self._threadIndex = ThreadIndex(self._path, mode)
            self._threadIndex_mode = mode
        return self._threadIndex

    def openMessageIDIndex(self, mode):
        if self._messageIDIndex is None or self._messageIDIndex_mode != mode:
            self._messageIDIndex = MessageIDIndex(self._path, mode)
            self._messageIDIndex_mode = mode
        return self._messageIDIndex

    def openAuthorIndex(self, mode):
        if self._authorIndex is None or self._authorIndex_mode != mode:
            self._authorIndex = AuthorIndex(self._path, mode)
            self._authorIndex_mode = mode
        return self._authorIndex

    def openSearchIndex(self, mode):
        if self._searchIndex is None or self._searchIndex_mode != mode:
            self._searchIndex = SearchIndex(self._path, mode)
            self._searchIndex_mode = mode
        return self._searchIndex

    def setConfig(self, k, v):
        self._config_dirty = 1
        self.config.setValue(k, v)

    ################################################################
    #### Message Helper Functions
    def parser(self):
        if self._parser is None:
            self._parser = Parser.Parser()
        return self._parser

    def references(self, msg, h_subject):
        refs = []
        ref_line = msg.get("References")
        if ref_line:
          ref_line = string.replace(ref_line, '\r', ' ')
          ref_line = string.replace(ref_line, '\n', ' ')
          ref_line = string.replace(ref_line, '\t', ' ')
          parts = string.split(ref_line)
          for part in parts:
            part = string.strip(part)
            if not part: continue
            m = re.search("<([^>]+)>", part)
            if m:   
                ref = m.group(1)
                if ref not in refs:
                    refs.append(ref)
        h_inreply = msg.get("In-Reply-To")
        if h_inreply:
            h_inreply = string.strip(h_inreply)
            if h_inreply:
              m = re.search("<([^>]+)>", h_inreply)
              if m:   
                  ref = m.group(1)
                  if ref not in refs:
                      refs.insert(0, ref)
        msg_id = None
        h_msg_id = msg.get("Message-ID")
        if h_msg_id:
            m = re.search("<([^>]+)>", h_msg_id)
            if m:   msg_id = m.group(1)

        h_subject = reduce_subject(h_subject)
        if len(h_subject) > 9:
            subj_id = "subj:%s" % (str(abs(hash(h_subject))))
            refs.append(subj_id)
        else:
            subj_id = None
        return msg_id, subj_id, refs

    def summary(self, msgobj):
        SUMMARY_LENGTH = 50
        # We're looking for the first SUMMARY_LENGTH chars of original text
        rm = email_message.RenderMessage(mimemsg=msgobj)
        data = rm.as_text()
        lines = data.split('\n')
        quote_regexp = "([ \t]*[|>:}#])+"
        header_regexp = "(From|Subject|Date): "
        quote_re = re.compile(quote_regexp)
        header_re = re.compile(header_regexp)
        dash_re = re.compile('------')
        summary = []
        summary_length = 0
        found_quoted = 0
        for line in lines:
            if quote_re.match(line):
                found_quoted = 1
            elif header_re.match(line):
                found_quoted = 1
            elif line.find('Original Message') != -1:
                break
            elif dash_re.search(line):
                found_quoted = 1
            else:
                if found_quoted:
                    summary.append('...')
                    found_quoted = 0
                summary.append(line)
                summary_length += len(line)
                if summary_length > SUMMARY_LENGTH:
                    break
        return " ".join(summary) + '...'

    def lock(self):
        pass

    def unlock(self):
        pass

    ################################################################
    #### Data Write
    def insertMessage(self, msg_data):
        # Ok, inserting a message is a bit of a mess... we have 7 data
        # sets to maintain based on the message data (what I wouldn't do for a
        # database...)
        # 1) Parse the message, and get: 
        #   - message id, subj_id, references
        #   - author, subject, date
        #   - summary
        m = self.parser().parsestr(msg_data)
        rm = email_message.RenderMessage(mimemsg=m)
        h_subj = rm.decode_header(m, 'subject', as_utf8 = 1)

        msg_id, subj_id,  references = self.references(m, h_subj)
        h_date = rm.decode_header(m, 'date', as_utf8 = 0)
        date_t = 0
        if h_date:
            tup = date.parsedate_tz(h_date)
            try:
                date_t = date.mktime_tz(tup)
            except (ValueError, OverflowError):
                pass

        h_from = rm.decode_header(m, 'from', as_utf8 = 1)
        from_adr_obj = rfc822.AddressList(h_from)
        if len(from_adr_obj):
            from_name, from_addr = from_adr_obj.addresslist[0]
        else:
            from_name, from_addr = "", ""
        summary = self.summary(m)

        # 2) Lookup reference information to determine thread id and parent
        # Let's see if this message refers to any message we've 
        # seen before...
        msgid_idx = self.openMessageIDIndex('w')
        parent_id = msgid_idx.find(references)

        doc_id = self.config.getIntValue("MaxDocID", 0)
        doc_id = doc_id + 1
        self.setConfig("MaxDocID", str(doc_id))

        if parent_id == 0:
            thread_id = self.config.getIntValue("MaxThreadID", 0)
            thread_id = thread_id + 1
            self.setConfig("MaxThreadID", str(thread_id))
        else:
            thread_id = 0

        # 3) Write message
        # 4) Write message index entry
        # 5) Update parent or sibling entry (ie, next or child)
        msg_idx = self.openMessageIndex('w')
        thread_id = msg_idx.add(doc_id, msg_data, parent_id, thread_id, date_t, h_subj, from_name, from_addr)

        # 6) Update thread index
        thr_idx = self.openThreadIndex('w')
        thr_idx.add(thread_id, doc_id)

        # 7) Update Msgid Index
        if msg_id:
            msgid_idx.add(msg_id, doc_id)
        if subj_id:
            msgid_idx.add(subj_id, doc_id)

        # 8) Update Summary
        msgsum_idx = self.openMessageSummary('w')
        msgsum_idx.add(doc_id, summary)

        # 9) Update by month
        bymonth = self.openByMonth()
        bymonth.add(doc_id, date_t)

        # 10) Update authors
        author_idx = self.openAuthorIndex('w')
        author_idx.add(from_name, from_addr, date_t)

        # 11) Update search
        search_idx = self.openSearchIndex('w')
        search_idx.add(doc_id, m, from_addr)

    ################################################################
    #### Data Read Functions
    def messageIndex(self, start, count):
        max = self.config.getIntValue("MaxDocID", 0)
        if start < 0:
            start = start + max + 1
        if start + count > max:
            count = max - start + 1

        msg_idx = self.openMessageIndex('r')
        idxs = []
        while count:
            idxs.append(msg_idx.get(start))
            start = start + 1
            count = count - 1
        return idxs

    def message(self, num, full=0, summary=0, snippet_for=None):
        max = self.config.getIntValue("MaxDocID", 0)
        if num < 0:
            num = num + max + 1
        if num > max:
            raise eNoMessage

        if snippet_for:
            # we need the full message
            full=1

        msg_idx = self.openMessageIndex('r')
        msg = msg_idx.get(num, full = full)

        # this is not computing a real snippit. This is
        # just the precomputed summary

        if summary:
            msgsum_idx = self.openMessageSummary('r')
            msg.summary = msgsum_idx.get(num)

        if snippet_for:
            snippet  = search_help.Snippet()
            
            m = self.parser().parsestr(msg.msg_data)
            rm = email_message.RenderMessage(mimemsg=m)
            msg.snippet = snippet.snippet(snippet_for, rm.as_text())


        return msg

    def thread_count(self, thread_id):
        max = self.config.getIntValue("MaxThreadID", 0)
        if thread_id < 0:
            thread_id = thread_id + max + 1
        if thread_id > max:
            return 0

        thr_idx = self.openThreadIndex('r')
        return len(thr_idx.get(thread_id))

    def thread(self, thread_id):
        max = self.config.getIntValue("MaxThreadID", 0)
        if thread_id < 0:
            thread_id = thread_id + max + 1
        if thread_id > max:
            raise eNoMessage

        thr_idx = self.openThreadIndex('r')
        dlist = thr_idx.get(thread_id)
        if len(dlist) == 0:
            raise eNoMessage

        msgs = []
        for num in dlist:
            msgs.append(self.message(int(num)))

        return msgs

    def search_author(self, email):
        srch_idx = self.openSearchIndex('r')
        log("search %s" % email)
        results = srch_idx.search("", ["AUTHOR:%s" % email.lower()])
        log(str(results))

        msgs = []
        for num in results:
            msgs.append(self.message(int(num), full=1))

        return msgs

    def search(self, query, start = None, count = None):
        srch_idx = self.openSearchIndex('r')
        results = srch_idx.search(query)

        msgs = []
        if start is None:
            partial = results
        else:
            partial = results[start:start + count]

        for num in partial:
            msgs.append(self.message(int(num), full=1,snippet_for=query))

        return len(results), msgs

    def counts(self):
        max_thread = self.config.getIntValue("MaxThreadID", 0)
        max_doc = self.config.getIntValue("MaxDocID", 0)
        return max_doc, max_thread

def strip_re(subject_string, subj_prefix = None):
    if subj_prefix:
        subject_string = subject_string.replace(subj_prefix, '')
    subject_string = re.sub("\s+", " ", subject_string)
    subject_string = string.strip(subject_string)
    re_re = re.compile("(re([\\[0-9\\]+])*|aw):[ \t]*(.*)", re.IGNORECASE)
    match = re_re.match(subject_string)
    while match:
        subject_string = match.group(3)
        match = re_re.match(subject_string)

    return string.strip(subject_string)

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
