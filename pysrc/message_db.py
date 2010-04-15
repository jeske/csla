
import os, sys, string, re, time
import marshal
import subprocess

from clearsilver import odb, hdfhelp, odb_sqlite3
from clearsilver.log import *

import neo_cgi, neo_util
import email_message
from mimelib import Message, Generator, Parser, date
import rfc822

import SwishE

import search_help

eNoMessage = "eNoMessage"

class Message(odb.Row):
    def subclassinit(self):
      self.snippet = None
       
    def hdfExport(self, prefix, hdf, tz="US/Pacific", subj_prefix=None):
        hdf.setValue(prefix, "1")
        obj = hdf.getObj(prefix)
        obj.setValue("doc_id", str(self.doc_id))
        obj.setValue("thread_id", str(self.thread_id))
        obj.setValue("parent_id", str(self.parent_id))
        obj.setValue("next_id", str(self.next_id))
        obj.setValue("child_id", str(self.child_id))
        if self.date:
            neo_cgi.exportDate(obj, "date", tz, self.date)

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

class MessageIndex(odb.Database):
    # Maps message number to message meta information
    def __init__ (self, conn):
      odb.Database.__init__(self, conn)
      self.addTable("messages", "ds_messages", MessageTable, rowClass=Message)

    def defaultRowClass(self):
      return hdfhelp.HdfRow
    def defaultRowListClass(self):
      return hdfhelp.HdfItemList

    def add(self, doc_id, msg_data, parent_id, thread_id, date_t, 
            h_subj, author, email, summary):

        parent_meta = None
        if thread_id == 0:
          parent_meta = self.get(parent_id)
          if parent_meta:
            thread_id = parent_meta.thread_id

        row = self.messages.newRow()
        row.doc_id = doc_id
        row.thread_id = thread_id
        row.parent_id = parent_id
        row.next_id = 0
        row.child_id = 0
        row.date = date_t
        row.subject = h_subj
        row.summary = summary
        row.author = author
        row.email = email
        row.msg_data = msg_data


        
        row.save()

        if parent_meta is not None:
            if parent_meta.child_id == 0:
              parent_meta.child_id = doc_id
              parent_meta.save()
            else:
              child_meta = self.get(parent_meta.child_id)
              while child_meta.next_id:
                child_meta = self.get(child_meta.next_id)

              child_meta.next_id = doc_id
              child_meta.save()

        return thread_id

    def get(self, doc_id):
      return self.messages.lookup(doc_id=doc_id)


class MessageTable(odb.Table):

  def _defineRows(self):
    self.d_addColumn("doc_id",odb.kInteger,None,primarykey = 1,
                     autoincrement = 1)
    self.d_addColumn("thread_id",odb.kInteger)
    self.d_addColumn("parent_id",odb.kInteger)
    self.d_addColumn("child_id",odb.kInteger)
    self.d_addColumn("next_id",odb.kInteger)
    self.d_addColumn("date",odb.kInteger)
    self.d_addColumn("subject",odb.kVarString)
    self.d_addColumn("summary",odb.kVarString)
    self.d_addColumn("author",odb.kVarString)
    self.d_addColumn("email",odb.kVarString)
    
    self.d_addColumn("msg_data",odb.kBigString,None, compress_ok=1)

    


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
        


class ThreadIndexTable(odb.Table):
  def _defineRows(self):
    self.d_addColumn("thread_id",odb.kVarString,None,primarykey = 1)
    self.d_addColumn("doc_list",odb.kVarString,None)

class ThreadRow(odb.Row):
  def getDocList(self):
    if self.doc_list is None: return []
    return string.split(self.doc_list, ',')
  def setDocList(self,dlist):
    self.doc_list = string.join(dlist, ',')

class ThreadIndex(odb.Database):
    # Maps thread ids to message numbers
    def __init__ (self, conn):
      odb.Database.__init__(self, conn)
      self.addTable("threads", "ds_threads", ThreadIndexTable, rowClass=ThreadRow)

    def add(self, thread_id, doc_id):
      row = self.threads.lookupCreate(thread_id=thread_id)
      dlist = row.getDocList()
      dlist.append(str(doc_id))
      row.setDocList(dlist)
      row.save()

    def get(self, thread_id):
      row = self.threads.lookup(thread_id=thread_id)
      return row

class MessageIDTable(odb.Table):
  def _defineRows(self):
    self.d_addColumn("msg_id",odb.kVarString,None,primarykey = 1)
    self.d_addColumn("doc_id",odb.kInteger,None)

class MessageIDIndex(odb.Database):
    # Maps message ids to message numbers
    def __init__ (self, conn):
      odb.Database.__init__(self, conn)
      self.addTable("messageidx", "ds_messageidx", MessageIDTable)
      

    def find(self, references):
      for ref in references:
        row = self.messageidx.lookup(msg_id=ref)
        if row: return row.doc_id
      return 0

    def add(self, msg_id, doc_id):
      
      row = self.messageidx.newRow(replace=1)
      row.msg_id = msg_id
      row.doc_id = doc_id
      row.save()

class AuthorTable(odb.Table):
  def _defineRows(self):
    self.d_addColumn("email",   odb.kVarString,None,primarykey = 1)
    self.d_addColumn("name",  odb.kVarString)
    self.d_addColumn("bymonth", odb.kVarString)

class AuthorRow(odb.Row):
  def getByMonth(self):
    if self.bymonth is None: return {}
    mon_data = self.bymonth.split(' ')
    bymonth = {}
    for part in mon_data:
        (date, count) = part.split(':')
        bymonth[date] = int(count)
    return bymonth
  def setByMonth(self, bymonthDict):
    self.bymonth = string.join(map(lambda x: '%s:%d' % x, bymonthDict.items()))    

class AuthorIndex(odb.Database):
    # Maps email address to name and posts by month
    def __init__ (self, conn, path):
      odb.Database.__init__(self, conn)
      self.addTable("authors", "ds_authors", AuthorTable, rowClass=AuthorRow)
      self._path = path


    def add(self, author, email, date_t):
        if not email: return
        email = email.strip()
        lemail = email.lower()

        tup = time.localtime(date_t)
        year = tup[0]
        mon = tup[1]
        date = '%s-%02d' % (year, mon)

        row = self.authors.lookupCreate(email=lemail)
        name = row.name
        bymonth = row.getByMonth()

        #(junk, name, bymonth) = self.get(email)
        if not author:
            author = name
        total = bymonth.get('total', 0)
        total += 1
        bymonth['total'] = total
        count = bymonth.get(date, 0)
        count += 1
        bymonth[date] = count

        row.setByMonth(bymonth)
        if author is None: author = "no author"
        row.name = author
        row.save()

        if 1:
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
      lemail = email.lower()
      row = self.authors.lookup(email=lemail)
      return row


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

global flag
flag = 0

class SearchIndex:
    # Full text index of the messages
    def __init__ (self, path, mode):
        self._rtv = None
        self._path = path
        self._search_path = os.path.join(self._path, "search")
        if not os.path.exists(self._search_path):
          os.mkdir(self._search_path, 0700)

        self._configfn = os.path.join(self._search_path, "config")
        self._indexfn = os.path.join(self._search_path, "index")

        if not os.path.exists(self._configfn):
          fp = open(self._configfn, "w")
          fp.write("IndexFile %s\n" % self._indexfn)
          fp.write("StoreDescription TXT* 10000\n")
          fp.write("StoreDescription HTML* <body> 10000\n")
          fp.write("MetaNames subject author\n")
          fp.close()

        self._stdin = None

        if mode == 'w':
          cmd = ["swish-e", "-c", self._configfn, "-S", "prog", "-i", "stdin"]
          rtv = subprocess.Popen(cmd, stdin=subprocess.PIPE)
          self._stdin = rtv.stdin
        else:
          rtv = SwishE.new(self._indexfn)
        self._rtv = rtv
        self._rtv_count = 0

    def _write(self, s):
      self._stdin.write(s)
      self._stdin.write("\n")
    def _writeln(self):
      self._stdin.write("\n")
    
    def __del__ (self):
        self.close()

    def close(self):
        if self._rtv is not None:
          if self._stdin:
            self._rtv.stdin.close()
            self._rtv.wait()
          self._rtv = None

    def add(self, msg_num, msgobj, email):
        # Ok, time to index the actual message
        rm = email_message.RenderMessage(mimemsg=msgobj)

        self._write("Path-Name: %s" % (os.path.join(self._path, str(msg_num))))

        extra = []
        if 1:
          for hdr in ["subject"]:
              val = rm.decode_header(msgobj, hdr, "", as_utf8=1)
              if val: 
                extra.append('<meta name="%s" content="%s">' % (hdr, neo_cgi.htmlEscape(val)))
          extra.append('<meta name="author" content="%s">' % neo_cgi.htmlEscape(string.lower(email)))
        extra = string.join(extra, "\n")

        data = rm.as_text()
        data = neo_cgi.htmlEscape(data)

        data = data + extra

        self._write("Document-Type: HTML*")
        self._write("Content-Length: %s" % str(len(data)))
        self._writeln()
        
        self._rtv.stdin.write(data)

        self._rtv_count = self._rtv_count + 1


    def search(self, query, attrs=[]):
      search = self._rtv.search(query)
      results = search.execute(query)
      
      ret = []
      for result in results:
        path = result.getproperty("swishdocpath")
        base, num = os.path.split(path)
        ret.append(int(num))

      return ret


class MessageDB:
    def __init__ (self, path):
        self._path = path

        if not os.path.exists(self._path + '/archive'):
          os.makedirs(self._path + '/archive', 0777)


        self._messageIndex = None
        self._messageIndex_mode = None
        self._byMonth = None

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
        if os.path.exists(self._config_file):
            self.config.readFile(self._config_file)
        self._config_dirty = 0

        self._parser = None

    def createTables(self):
      import which_read
      which_read.createTables(self._path)

      for openCmd in (self.openMessageIndex, self.openThreadIndex, 
                      self.openMessageIDIndex, self.openAuthorIndex):
        db = openCmd("rw")
        db.createTables()
        db.synchronizeSchema()
        db.createIndices()
      

    def __del__ (self):
        self.flush()

    def flush(self):
        if self._config_dirty:
            self.config.writeFile("%s/archive/mdb.hdf" % self._path)
            self._config_dirty = 0
        self._messageIndex = None
        self._messageIndex_mode = None
        self._byMonth = None
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
            apath = "%s/archive/msgidx.db3" % self._path
#            conn = odb_sqlite3.Connection(apath, autocommit=0)
            conn = odb_sqlite3.Connection(apath)
            self._messageIndex = MessageIndex(conn)
            self._messageIndex_mode = mode
        return self._messageIndex

    def openByMonth(self):
        if self._byMonth is None:   
            self._byMonth = ByMonth(self._path)
        return self._byMonth


    def openThreadIndex(self, mode):
        if self._threadIndex is None or self._threadIndex_mode != mode:
            apath = "%s/archive/threadidx.db3" % self._path
#            conn = odb_sqlite3.Connection(apath, autocommit=0)
            conn = odb_sqlite3.Connection(apath)
            self._threadIndex = ThreadIndex(conn)
            self._threadIndex_mode = mode
        return self._threadIndex

    def openMessageIDIndex(self, mode):
        if self._messageIDIndex is None or self._messageIDIndex_mode != mode:
            apath = "%s/archive/msgids.db3" % self._path
#            conn = odb_sqlite3.Connection(apath, autocommit=0)
            conn = odb_sqlite3.Connection(apath)
            self._messageIDIndex = MessageIDIndex(conn)
            self._messageIDIndex_mode = mode
        return self._messageIDIndex

    def openAuthorIndex(self, mode):
        if self._authorIndex is None or self._authorIndex_mode != mode:
            apath = "%s/archive/authors.db3" % self._path
#            conn = odb_sqlite3.Connection(apath, autocommit=0)
            conn = odb_sqlite3.Connection(apath)
            self._authorIndex = AuthorIndex(conn, self._path)
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
        thread_id = msg_idx.add(doc_id, msg_data, parent_id, thread_id, date_t, h_subj, from_name, from_addr, summary)

        # 6) Update thread index
        thr_idx = self.openThreadIndex('w')
        thr_idx.add(thread_id, doc_id)

        # 7) Update Msgid Index
        if msg_id:
          msgid_idx.add(msg_id, doc_id)
        if subj_id:
          msgid_idx.add(subj_id, doc_id)


        # 9) Update by month
        bymonth = self.openByMonth()
        bymonth.add(doc_id, date_t)

        # 10) Update authors
        author_idx = self.openAuthorIndex('w')
        author_idx.add(from_name, from_addr, date_t)

        # 11) Update search
        if 1:
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
        msg = msg_idx.get(num)


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
        thr = thr_idx.get(thread_id)
        dlist = thr.getDocList()
        if len(dlist) == 0:
            raise eNoMessage

        msgs = []
        for num in dlist:
            msgs.append(self.message(int(num)))

        return msgs

    def search_author(self, email):
        srch_idx = self.openSearchIndex('r')
        log("search %s" % email)
        results = srch_idx.search("author=(%s)" % email.lower())
        log(str(results))

        msgs = []
        for num in results:
            msgs.append(self.message(int(num), full=1))

        return msgs

    def search(self, query, start = None, count = None):
        srch_idx = self.openSearchIndex('r')
        results = srch_idx.search(query)

        partial = results
        msgs = []
        if start is None:
          partial = results
        else:
          partial = results[start:start+count]

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
