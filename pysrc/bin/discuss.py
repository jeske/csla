#!/neo/opt/bin/python

import sys, string, os, time, math

import nstart

import CSPage
import message_db
from email_message import RenderMessage
import neo_cgi, neo_rtv
from wordwrap import WordWrap
from log import *
import profiler
import cache
import urllib

import email_message

import which_read

import search_help

DISCUSS_DATA_ROOT = "/home/discuss/data"
VISIT_DURATION = 3600 * 6   # 6 hours

class DiscussPage(CSPage.CSPage):
    def setup(self):
        self.mdb = None
        self.listname = None
        self.index_page_num = 0
        self.index_pages = {}
        self.index_pages_by = 10
        self.threads = 0
        self.mcache = None
        self.tz = "US/Pacific"

        # Determine URI Root
        scn = self.ncgi.hdf.getValue("CGI.ScriptName", "")
        if not scn: 
            scn = '/'
        else:
            if scn[-11:] == "/discuss.py":
                scn = scn[:-11]
            if scn[-1] != '/': scn = scn + '/'
        self.ncgi.hdf.setValue("CGI.URIRoot", scn)

        self.path_info = filter(None, string.split(self.ncgi.hdf.getValue("CGI.PathInfo", ""), '/'))
        n = 0
        for part in self.path_info:
            self.ncgi.hdf.setValue("CGI.PathInfo.%d" % n, part)
            n += 1
        self.load_list()
        
        if self.listname:
            self.determine_page()
            self.check_visit_cookie()
        else:
            self.pagename = "archives"

        self.check_tz_cookie()
        self.check_prefs_cookie()

        self.whichread = which_read.WhichRead(self.listname,self.getListDataPath(),self.ncgi)

    def check_tz_cookie(self): 
        self.tz = self.ncgi.hdf.getValue("Cookie.TZ", self.tz)
        self.ncgi.hdf.setValue("CGI.TimeZone", self.tz)

    def check_prefs_cookie(self):
        # default prefs
        self.browse_type = "frame"
        self.multi_msg = 0

        # Read prefs from cookie
        prefs_cookie = self.ncgi.hdf.getValue("Cookie.DPrefs", "")
        if prefs_cookie:
            parts = prefs_cookie.split('&')
            for part in parts:
                try:
                    (k, v) = part.split('=', 1)
                except ValueError:
                    k = part
                    v = "1"
                if k == "v": # version
                    pass
                elif k == "browse":
                    if v in ["frame", "iframe", "noframes"]:
                        self.browse_type = v
                elif k == "multi":
                    try:
                        self.multi_msg = int(v)
                    except ValueError:
                        self.multi_msg = 0

        # Ok, some HDf settings based on prefs
        self.ncgi.hdf.setValue("CGI.Prefs.Browse", self.browse_type)
        if self.browse_type == "frame":
            self.ncgi.hdf.setValue("CGI.BrowseUri", "browse_frm")
        elif self.browse_type == "iframe":
            self.ncgi.hdf.setValue("CGI.BrowseUri", "browse_ifrm")
        elif self.browse_type == "noframes":
            self.ncgi.hdf.setValue("CGI.BrowseUri", "browse")
        self.ncgi.hdf.setValue("CGI.Prefs.MultiMsg", str(self.multi_msg))
        if self.multi_msg:
            self.index_pages_by = 10
        else:
            self.index_pages_by = 1
                        
    def check_visit_cookie(self):
        ncgi = self.ncgi
        hdf = self.ncgi.hdf
        visit_cur = hdf.getValue("Cookie.%s.visit_cur" % self.listname,"")
        visit_last = hdf.getValue("Cookie.%s.visit_last" % self.listname,"")

        max_doc, max_thread = self.mdb.counts()
        new_cookie = "%s:%s:%s" % (int(time.time()),max_doc,max_thread)

        if not visit_cur:
            ncgi.cookieSet("%s.visit_cur" % self.listname,new_cookie,persist=1)
        else:
            log("%s.visit_cur: %s" % (self.listname,visit_cur))
            try:
                a_time,max_mnum,max_tid = string.split(visit_cur,":")
                if (time.time() - int(a_time)) > VISIT_DURATION:
                    ncgi.cookieSet("%s.visit_last" % self.listname,visit_cur)

                    ncgi.cookieSet("%s.visit_cur" % self.listname,new_cookie,persist=1)
                    hdf.setValue("Cookie.%s.visit_last" % self.listname,visit_cur)
                    hdf.setValue("Cookie.%s.visit_cur" % self.listname,new_cookie)
            except:
                ncgi.cookieSet("%s.visit_cur" % self.listname,new_cookie,persist=1)

    def Action_SetTimezone(self):
        q_tz = self.ncgi.hdf.getValue("Query.timezone", self.tz)
        if q_tz == "default":
            self.ncgi.cookieClear("TZ")
        else:
            self.ncgi.cookieSet("TZ", q_tz, persist=1)

        uri_root = self.ncgi.hdf.getValue("CGI.URIRoot", "/")
        self.redirectUri("%s%s" % (uri_root, self.listname))

    def Action_SetPrefs(self):
        q_tz = self.ncgi.hdf.getValue("Query.timezone", self.tz)
        if q_tz == "default":
            self.ncgi.cookieClear("TZ")
        else:
            self.ncgi.cookieSet("TZ", q_tz, persist=1)

        q_browse_style = self.ncgi.hdf.getValue("Query.browse_style", self.browse_type)
        if q_browse_style not in ["frame", "iframe", "noframes"]:
            q_browse_style = "noframes"

        q_multi_msg = self.ncgi.hdf.getIntValue("Query.multi_msg", 0)

        self.ncgi.cookieSet("DPrefs", "v=1&browse=%s&multi=%d" % (q_browse_style, q_multi_msg), persist=1)


        wr_key = self.ncgi.hdf.getValue("Query.whichread_key", "")
        if wr_key:
            wr_key = string.replace(wr_key," ","_") # escape space
            self.ncgi.hdf.setValue("Cookie.WRID",wr_key)
            self.ncgi.cookieSet("WRID",wr_key,persist=1)
           
            # clear the whichread cookies
            obj = self.ncgi.hdf.getObj("Cookie.WR")
            if obj:
                obj = obj.child()
                while obj:
                    cookiename = "WR.%s" % obj.name()
                    log("clear cookie: %s" % cookiename)
                    self.ncgi.cookieClear(cookiename)
                    obj = obj.next()

        # end and redirect
        uri_root = self.ncgi.hdf.getValue("CGI.URIRoot", "/")
        self.redirectUri("%s%s" % (uri_root, self.listname))

    def getListDataPath(self):
        return "%s/%s" % (DISCUSS_DATA_ROOT, self.listname)

    def load_list(self):
        if len(self.path_info) > 0:
            self.listname = self.path_info[0]
            self.listpath = os.path.join(DISCUSS_DATA_ROOT, self.listname)
            if not os.path.isdir(self.listpath):
                raise "List %s not found" % self.listname

            self.ncgi.hdf.setValue("CGI.ArchiveName", self.listname)
            self.mdb = message_db.MessageDB("%s/%s" % (DISCUSS_DATA_ROOT, self.listname))
            self.ncgi.hdf.setValue("CGI.List", self.listname)
            obj = self.ncgi.hdf.getObj("CGI.List")
            obj.readFile("%s/list.hdf" % self.listpath)
            style = obj.getObj("Style")
            if style:
              self.ncgi.hdf.copy("",obj)
            self.tz = self.ncgi.hdf.getValue("CGI.List.TimeZone", self.tz)

    def determine_page(self):
        if self.listname is None:
            self.pagename = "archives"
        else:
            self.pagename = "home"

        if len(self.path_info) > 1:
            self.pagename = self.path_info[1]
        else:
            pass


    def display_index_bydate(self):
        self.pagename = "index"
        DISPLAY_COUNT = 50
        if len(self.path_info) > 2:
            try:
                start = int(self.path_info[2])
            except ValueError:
                start = -DISPLAY_COUNT
        else:
            start = -DISPLAY_COUNT
        idxs = self.mdb.messageIndex(start, DISPLAY_COUNT)

        n = 0
        for idx in idxs:
            idx.hdfExport("CGI.Index.%s" % n, self.ncgi.hdf, tz=self.tz)
            n = n + 1

        max_doc, max_thread = self.mdb.counts()
        first = int(idxs[0].doc_id)
        last = int(idxs[-1].doc_id)
        if first > 1:
            prev = first - DISPLAY_COUNT
            if prev < 1: prev = 1
            self.ncgi.hdf.setValue("CGI.Prev", str(prev))
        if last < max_doc:
            next = last + 1
            self.ncgi.hdf.setValue("CGI.Next", str(next))
        self.ncgi.hdf.setValue("CGI.First", str(first))
        self.ncgi.hdf.setValue("CGI.Last", str(last))
        self.ncgi.hdf.setValue("CGI.Total", str(max_doc))

    def openMessageCache(self):
        if self.mcache is None:
            self.mcache = cache.MessageCache(self.listpath)
        return self.mcache

    def export_msg_data(self, msg, prefix, hdf):
        self.openMessageCache()
        try:
            log("%d" % msg.doc_id)
            self.mcache.get(msg.doc_id, prefix, hdf)
            # ok, override the date in the cache
            date_t = hdf.getIntValue(prefix + ".date_t", 0)
            log("date_t is %s" % date_t)
            if date_t:
                neo_cgi.exportDate(hdf, "%s.h_date" % prefix, self.tz, date_t)
                neo_cgi.exportDate(hdf, "TestDate", self.tz, date_t)
        except cache.eNotCached:
            rm = RenderMessage(rawmsg = msg.msg_data, tz=self.tz)
            uri_root = self.ncgi.hdf.getValue("CGI.URIRoot", "/")
            attach_url_base = "%s%s/attach/%s/%%s" % (uri_root, self.listname, msg.doc_id)
            rm.export_message(prefix, hdf, attach_str=attach_url_base)
            self.mcache.store(msg.doc_id, prefix, hdf)

    def display_attachment(self):
        self.pagename = "attach"

        if len(self.path_info) > 3:
            try:
                num = int(self.path_info[2])
            except ValueError:
                num = -1

        else:
            raise "invalid attachment URL"

        attachname = urllib.unquote(string.join(self.path_info[3:],"/"))
        log("attach name: %s" % attachname)

        meta = self.mdb.message(num, full=1)
        rm = RenderMessage(rawmsg=meta.msg_data, tz=self.tz)
        ct,body,name = rm.part_content(attachname)
        if ct and body:
            self.output("Content-Type: %s\r\n\r\n" % ct)
            self.output(body)
        else:
            log("didn't find it")

        raise CSPage.DisplayDone, "Attachment displayed"
        

    def display_msg(self):
        hdf = self.ncgi.hdf
        self.pagename = "msg"

        if len(self.path_info) > 2:
            try:
                num = int(self.path_info[2])
            except ValueError:
                num = -1
        else:
            num = -1

        meta = self.mdb.message(num, full=1)
        meta.hdfExport("CGI.Msg.Meta", self.ncgi.hdf,tz=self.tz)
        if hdf.getValue("Query.dmode","") == "source":
            hdf.setValue("CGI.Msg.Message.RAWDATA",email_message.maskAddr(meta.msg_data))
        else:
            self.export_msg_data(meta, "CGI.Msg.Message", self.ncgi.hdf)
            
        count = self.mdb.thread_count(meta.thread_id)
        self.ncgi.hdf.setValue("CGI.Msg.Meta.thread_count", str(count))

        self.whichread.markMsgRead(num)

    def display_messages(self):
        hdf = self.ncgi.hdf
        self.pagename = "messages"

        if len(self.path_info) > 2:
            try:
                mlist = self.path_info[2].split(',')
                new_mlist = []
                for num in mlist:
                    try:
                        num = int(num)
                        new_mlist.append(num)
                    except ValueError:
                        pass
                mlist = new_mlist
            except IndexError:
                mlist = range(-10,0)
        else:
            mlist = range(-10,0)

        for num in mlist:
            meta = self.mdb.message(num, full=1)
            meta.hdfExport("CGI.Messages.%d.Meta" % num, self.ncgi.hdf, tz=self.tz)
            count = self.mdb.thread_count(meta.thread_id)
            self.ncgi.hdf.setValue("CGI.Messages.%d.Meta.thread_count" % num, str(count))
            if hdf.getValue("Query.dmode","") == "source":
                hdf.setValue("CGI.Messages.%d.Message.RAWDATA" % num,meta.msg_data)

            self.export_msg_data(meta, "CGI.Messages.%d.Message" % num, self.ncgi.hdf)
            self.whichread.markMsgRead(num)

    def display_threads(self):
        self.pagename = "threads"
        THREAD_COUNT = 25
        hdf = self.ncgi.hdf
        subj_prefix = self.ncgi.hdf.getValue("CGI.List.SubjectPrefix", "")
        q_start = hdf.getIntValue("Query.start",1)

        max_doc, max_thread = self.mdb.counts()

        hdf.setValue("CGI.ThreadsPage.Count","%s" % THREAD_COUNT)
        hdf.setValue("CGI.ThreadsPage.CurStart","%s" % q_start)
        hdf.setValue("CGI.ThreadsPage.MaxThreadNum","%s" % max_thread)

        has_next_page = 1
        last_thread = q_start
        for x in range(q_start,q_start + THREAD_COUNT):
            try:
                msgs = self.mdb.thread(-1 * x)
                msgs[-1].hdfExport("CGI.Threads.%d" % x, self.ncgi.hdf,tz=self.tz,subj_prefix=subj_prefix)
                self.ncgi.hdf.setValue("CGI.Threads.%d.count" % x, str(len(msgs)))
                last_thread = x
            except message_db.eNoMessage:
                has_next_page = 0
                pass
        hdf.setValue("CGI.ThreadsPage.CurEnd","%s" % last_thread)

        if has_next_page:
            hdf.setValue("CGI.ThreadsPage.NextStart","%s" % (q_start + THREAD_COUNT))
        if q_start > 1:
            prev_start = q_start - THREAD_COUNT
            if prev_start < 1:
                prev_start = 1
            hdf.setValue("CGI.ThreadsPage.PrevStart","%s" % prev_start)

    def _add_msg_to_page(self, msg, prefix):
        if not self.index_pages.has_key(self.index_page_num):
            self.index_pages[self.index_page_num] = []

        if msg.doc_id in self.index_pages[self.index_page_num]:
            self.ncgi.hdf.setValue(prefix + ".page", str(self.index_page_num))
            return

        if len(self.index_pages[self.index_page_num]) == self.index_pages_by:
            self.index_page_num += 1
            self.index_pages[self.index_page_num] = []

        self.index_pages[self.index_page_num].append(msg.doc_id)
        self.ncgi.hdf.setValue(prefix + ".page", str(self.index_page_num))

    def export_pages(self):
        for x in range(self.index_page_num+1):
            try:
                docs = map(str, self.index_pages[x])
                self.ncgi.hdf.setValue("CGI.Index.MsgPage.%d" % x, ','.join(docs))
            except KeyError:
                break

    def export_thread_index(self, msgs, prefix):
        # Arrange hierarchically
        msg_d = {}
        top = None
        for msg in msgs:
            msg_d[msg.doc_id] = msg
            if msg.parent_id == 0:
                top = msg

        subj_prefix = self.ncgi.hdf.getValue("CGI.List.SubjectPrefix", "")

        def export_part(msg_map, parent_id, prefix):
            current_id = msg_map[parent_id].child_id
            n = 0
            while current_id:
                try:
                    msg = msg_map[current_id]
                except KeyError:
                    # this implies that this thread continues past what we have
                    break
                msg.hdfExport("%s.%d" % (prefix, n), self.ncgi.hdf, tz=self.tz, subj_prefix=subj_prefix)
                self._add_msg_to_page(msg, "%s.%d" % (prefix, n))
                if msg.child_id:
                    export_part(msg_map, current_id, "%s.%d.children" % (prefix, n))
                current_id = msg.next_id
                n += 1

        if top is None:
            # Ok, this is a partial thread, let's do our best...
            tops = []
            for msg in msgs:
                if not msg_d.has_key(msg.parent_id):
                    tops.append(msg)
            for top in tops:
                thr_prefix = prefix + ".%d" % (self.threads)
                top.hdfExport(thr_prefix, self.ncgi.hdf, tz=self.tz, subj_prefix=subj_prefix)
                self._add_msg_to_page(top, thr_prefix)
                export_part(msg_d, top.doc_id, thr_prefix + ".children")
                self.threads += 1
        else:
            thr_prefix = prefix + ".%d" % (self.threads)
            top.hdfExport(thr_prefix, self.ncgi.hdf, tz=self.tz, subj_prefix=subj_prefix)
            self._add_msg_to_page(top, thr_prefix)
            export_part(msg_d, top.doc_id, thr_prefix + ".children")
            self.threads += 1

    def display_index(self):
        self.pagename = "index"

        # There are a couple different modes here... for now, we're doing 
        # thread mode

        mode = "new"
        if len(self.path_info) > 2:
            mode = self.path_info[2]
            if mode == "thread":
                try:
                    thread_id = int(self.path_info[3])
                except (ValueError, IndexError):
                    thread_id = -1
            elif mode == "month":
                try:
                    month = self.path_info[3]
                except (ValueError, IndexError):
                    tup = time.localtime(time.time())
                    year = tup[0]
                    mon = tup[1]
                    month = '%s-%02d' % (year, mon)
                bym = self.mdb.openByMonth()
                (first_num, count) = bym.get(month)
            elif mode == "author":
                try:
                    email = self.path_info[3].lower()
                except IndexError:
                    email = ""
                try:
                    sub_mode = self.path_info[5]
                except IndexError:
                    sub_mode = None
                if sub_mode == "month":
                    try:
                        month = self.path_info[6]
                    except (ValueError, IndexError):
                        tup = time.localtime(time.time())
                        year = tup[0]
                        mon = tup[1]
                        month = '%s-%02d' % (year, mon)
            elif mode == "search":
                query = self.ncgi.hdf.getValue("Query.query", "")
                if not query:
                    uri_root = self.ncgi.hdf.getValue("CGI.URIRoot", "/")
                    self.redirectUri("%s%s/search" % (uri_root, self.listname))
            else:
                mode = "new"
                thread_id = -1
        else:
            thread_id = -1

        self.ncgi.hdf.setValue("CGI.IndexMode", mode)
        self.ncgi.hdf.setValue("CGI.DisplayMode", "thread")

        if mode == "new":
            for x in range(1,10):
                try:
                    msgs = self.mdb.thread(-1 * x)
                    self.export_thread_index(msgs, "CGI.Index.Threads")
                except message_db.eNoMessage:
                    pass
            self.export_pages()
        elif mode == "thread":
            msgs = self.mdb.thread(thread_id)
            self.export_thread_index(msgs, "CGI.Index.Threads")
            self.export_pages()

        elif mode == "month":
            idx_cache = cache.IndexCache(self.listpath)
            bym = self.mdb.openByMonth()
            firstnum,count = bym.get(month)
            inv_key = "%s:%s" % (firstnum,count)

            try:
                
                idx_cache.get(month, "CGI.Index", self.ncgi.hdf,inv_key=inv_key)
                log("using cached")
            except cache.eNotCached:
                threads = {}
                thread_date = {}
                num = first_num
                x = 0
                (year, mon) = month.split('-')
                year = int(year) 
                mon = int(mon)
    #            if count > 250:
    #                self.ncgi.hdf.setValue("CGI.Index.More", "1")
    #                count = 250 
                if self.debugEnabled:
                    p = profiler.Profiler("MDB", "Month Fetch: %d messages" % count)
                while x < count:
                    msg = self.mdb.message(num)
                    tup = time.localtime(msg.date_t)
                    if tup[0] == year and tup[1] == mon:
                        try:
                            threads[msg.thread_id].append(msg)
                        except KeyError:
                            threads[msg.thread_id] = [msg]
                        try:
                            if thread_date[msg.thread_id] > msg.date_t:
                                thread_date[msg.thread_id] = msg.date_t
                        except KeyError:
                            thread_date[msg.thread_id] = msg.date_t
                        x += 1
                    num += 1
                if self.debugEnabled: p.end()
                if self.debugEnabled:
                    p = profiler.Profiler("EXPORT", "Exporting threads")
                order_threads = []
                for thread_id, t_date in thread_date.items():
                    order_threads.append((t_date, thread_id))
                order_threads.sort()
                
                for t_date, thread_id in order_threads:
                    self.export_thread_index(threads[thread_id], "CGI.Index.Threads")
                if self.debugEnabled: p.end()
                self.export_pages()
                idx_cache.store(month, "CGI.Index", self.ncgi.hdf,inv_key=inv_key)

        elif mode == "author" or mode == "search":
            self.ncgi.hdf.setValue("CGI.DisplayMode", "author")
            subj_prefix = self.ncgi.hdf.getValue("CGI.List.SubjectPrefix", "")
            msgs = []
            if mode == "author":
                # Here, we search for the author
                msgs = self.mdb.search_author(email)
                authors = self.mdb.openAuthorIndex('r')
                (junk, name, junk) = authors.get(email)
                self.ncgi.hdf.setValue("CGI.Author.Name", neo_cgi.htmlEscape(name))
                self.ncgi.hdf.setValue("CGI.Author.Email", neo_cgi.htmlEscape(email))
            elif mode == "search":
                total, msgs = self.mdb.search(query)
                
            n = 0
            for msg in msgs:
                msg.hdfExport("CGI.Index.Messages.%d" % (n), self.ncgi.hdf, tz=self.tz, subj_prefix=subj_prefix)
                self._add_msg_to_page(msg, "CGI.Index.Messages.%d" % (n))
                n += 1
            self.export_pages()

        self.add_whichread_info()
        
    def add_whichread_info(self):
        # walk all of CGI.Index looking for "doc_id"
        hdf = self.ncgi.hdf

        node = hdf.getObj("CGI.Index")
        wrl = self.whichread.getWRList()

        def recurse(node):
            if node:
                while node:
                    docid = node.getValue("doc_id","")
                    if docid:
                        if wrl.isRead(docid):
                            node.setValue("doc_id.IsRead", "1")
                        else:
                            node.setValue("doc_id.IsRead", "0")

                    
                    recurse(node.child())
                    node = node.next()

        recurse(node)

    def display_search(self):
        RESULTS_PER_PAGE = 10

        self.pagename = "search"

        query = self.ncgi.hdf.getValue("Query.query", "")
        self.ncgi.hdf.setValue("CGI.query_url", neo_cgi.urlEscape(query))
        q_page = self.ncgi.hdf.getIntValue("Query.page", 1)
        start = (q_page - 1) * RESULTS_PER_PAGE
        if start < 0: start = 0
        if query:
            search_t = time.time()
            total, msgs = self.mdb.search(query, start, RESULTS_PER_PAGE)
            if total == 0:
                self.ncgi.hdf.setValue("CGI.SearchNoResults", "1")
            search_t = time.time() - search_t
            self.ncgi.hdf.setValue("CGI.SearchTime", "%5.2f" % search_t)
            self.ncgi.hdf.setValue("CGI.SearchStart", str(start+1))
            end = start+RESULTS_PER_PAGE
            if end > total:
                end = total
            self.ncgi.hdf.setValue("CGI.SearchEnd", str(end))
            self.ncgi.hdf.setValue("CGI.SearchTotal", str(total))
            pages = math.ceil(total*1.0/RESULTS_PER_PAGE)
            page = (start+1)/RESULTS_PER_PAGE + 1
            if pages > 20:
                # If we have more than 20 pages, only show the 20 around
                # the page we're looking at
                if page < 20:
                    self.ncgi.hdf.setValue("CGI.SearchPageStart", "1")
                    self.ncgi.hdf.setValue("CGI.SearchPageEnd", "20")
                elif page+10 > pages:
                    self.ncgi.hdf.setValue("CGI.SearchPageStart", str(pages-20))
                    self.ncgi.hdf.setValue("CGI.SearchPageEnd", str(pages))
                else:
                    self.ncgi.hdf.setValue("CGI.SearchPageStart", str(page-10))
                    self.ncgi.hdf.setValue("CGI.SearchPageEnd", str(page+10))
            else:
                self.ncgi.hdf.setValue("CGI.SearchPageStart", "1")
                self.ncgi.hdf.setValue("CGI.SearchPageEnd", str(pages))

            self.ncgi.hdf.setValue("CGI.SearchPages", str(pages))
            self.ncgi.hdf.setValue("CGI.SearchPage", str(page))

            n = 0
            for meta in msgs:
                meta.hdfExport("CGI.Matches.%d" % n, self.ncgi.hdf, tz=self.tz)
                count = self.mdb.thread_count(meta.thread_id)
                self.ncgi.hdf.setValue("CGI.Matches.%d.thread_count" % n, str(count))
                rm = RenderMessage(rawmsg = meta.msg_data, tz=self.tz)
                text = rm.as_text()
                snipper = search_help.Snippet()
                snippet = snipper.snippet(query, text)
                self.ncgi.hdf.setValue("CGI.Matches.%d.Snippet" % n, snippet)
                n = n + 1

    def display_home(self):
        self.pagename = "home"
        subj_prefix = self.ncgi.hdf.getValue("CGI.List.SubjectPrefix", "")
        
        # We need the bymonth data, the 5 most recent threads, the top authors 
        # this month and ever

        # DO NOT CACHE THIS RESULT (it contains read-status info)

        wrl = self.whichread.getWRList()

        self.mdb.openByMonth().hdfExport("CGI.ByMonth", self.ncgi.hdf, reverse=1)
        max_doc, max_thread = self.mdb.counts()
        for x in range(5):
            try:
                mnum = max_doc - x
                msg = self.mdb.message(mnum, summary = 1)
                msg.hdfExport("CGI.RecentMessages.%d" % x, self.ncgi.hdf,subj_prefix=subj_prefix, tz=self.tz)
                if wrl.isRead(mnum):
                    self.ncgi.hdf.setValue("CGI.RecentMessages.%d.doc_id.IsRead" % x, "1") 
                else:
                    self.ncgi.hdf.setValue("CGI.RecentMessages.%d.doc_id.IsRead" % x, "0") 
                
            except message_db.eNoMessage:
                pass


        authors = self.mdb.openAuthorIndex('r')
        tup = time.localtime(time.time())
        date = '%s-%02d' % (tup[0], tup[1])
        data = authors.get_top(date)
        n = 0
        self.ncgi.hdf.setValue("CGI.TopAuthors.NowDate", date)
        for (count, email) in data[:5]:
            (email, name, junk) = authors.get(email)
            self.ncgi.hdf.setValue("CGI.TopAuthors.Now.%d.email" % n, email)
            self.ncgi.hdf.setValue("CGI.TopAuthors.Now.%d.name" % n, name)
            self.ncgi.hdf.setValue("CGI.TopAuthors.Now.%d.count" % n, str(count))
            n += 1
        self.ncgi.hdf.setValue("CGI.TopAuthors.Now", str(n))
            
        data = authors.get_top('total')
        n = 0
        for (count, email) in data[:5]:
            (email, name, junk) = authors.get(email)
            self.ncgi.hdf.setValue("CGI.TopAuthors.Total.%d.email" % n, email)
            self.ncgi.hdf.setValue("CGI.TopAuthors.Total.%d.name" % n, name)
            self.ncgi.hdf.setValue("CGI.TopAuthors.Total.%d.count" % n, str(count))
            n += 1
        self.ncgi.hdf.setValue("CGI.TopAuthors.Total", str(n))

        # populate new post info
        max_doc,max_thread = self.mdb.counts()
        ranges = [100,250,500]
        n = 0
        for a_range in ranges:
            if max_doc > a_range:
                m_num = max_doc-a_range
                self.ncgi.hdf.setValue("CGI.NewPosts.%d.Range" % n,"%s" % a_range)
                self.ncgi.hdf.setValue("CGI.NewPosts.%d.doc_id" % n,"%s" % m_num)
                
                try:
                    meta = self.mdb.message(m_num)
                    neo_cgi.exportDate(self.ncgi.hdf, "CGI.NewPosts.%d.Date" % n, self.tz, meta.date_t)
                    n = n + 1
                except message_db.eNoMessage:
                    pass
                

        # populate last-visit info
        visit_last = self.ncgi.hdf.getValue("Cookie.%s.visit_last" % self.listname,"")
        if visit_last:
            max_doc, max_thread = self.mdb.counts()
            valid = 1
            try:
                time_t,o_max_doc,o_max_thread = string.split(visit_last,":")
            except:
                valid = 0

            if valid:
            
                self.ncgi.hdf.setValue("CGI.LastVisit.NewMessages","%s" % (max_doc-int(o_max_doc)))
                self.ncgi.hdf.setValue("CGI.LastVisit.NewThreads","%s" % (max_thread-int(o_max_thread)))
                neo_cgi.exportDate(self.ncgi.hdf, "CGI.LastVisit.Date", self.tz, int(time_t))


    def display_fullbrowse(self):
        self.pagename = "fullbrowse"
        self.display_index()
        self.display_menu()
        self.pagename = "fullbrowse"
        
    def display_browse(self):
        self.pagename = "browse_frm"

    def display_browse_ifrm(self):
        self.pagename = "browse_ifrm"
        self.display_index()
        self.display_menu()
        self.pagename = "browse_ifrm"

    def display_top_authors(self):
        self.pagename = "top_authors"
        q_date = self.ncgi.hdf.getValue("Query.date", "total")
        q_start_date = self.ncgi.hdf.getValue("Query.start_date","")

        authors = self.mdb.openAuthorIndex('r')
        data = authors.get_top(q_date)

        COLS_PER_PAGE = 8

        n = 0
        first_month = None
        last_month = None
        # export the info
        for (count, email) in data[:20]:
            (email, name, bymonth) = authors.get(email)
            self.ncgi.hdf.setValue("CGI.TopAuthors.%d.email" % n, email)
            self.ncgi.hdf.setValue("CGI.TopAuthors.%d.name" % n, name)
            months = bymonth.keys()
            months.remove('total')
            months.sort()
            months.reverse()
            if not first_month or first_month > months[-1]:
                first_month = months[-1]
            if not last_month or last_month < months[0]:
                last_month = months[0]
            for month in months:
                self.ncgi.hdf.setValue("CGI.TopAuthors.%d.%s" % (n, month), str(bymonth[month]))
            self.ncgi.hdf.setValue("CGI.TopAuthors.%d.total" % (n), str(bymonth.get('total', 0)))
            n += 1

        if q_start_date:
            last_month = q_start_date

        # now, export information about what months we're displaying
        if first_month:
            self.ncgi.hdf.setValue("CGI.Months.0", "total")
            if q_date == "total":
                self.ncgi.hdf.setValue("CGI.Months.0.hilight", "1")
            n = 1
            (fyear, fmon) = first_month.split('-')
            (lyear, lmon) = last_month.split('-')
            year = int(lyear)
            mon = int(lmon)
            fyear = int(fyear)
            fmon = int(fmon)

            bym = self.mdb.openByMonth()

            # compute previous month for "<< next" nav
            for a_col in range(1,COLS_PER_PAGE):
                next_mon = mon + a_col
                next_year = year
                while next_mon > 12:
                    next_mon = next_mon - 12
                    next_year = next_year + 1
                next_date = "%s-%02d" % (next_year,next_mon)
                bym_firstnum,bym_count = bym.get(next_date)
                if bym_count > 0:
                    self.ncgi.hdf.setValue("CGI.MonthPage.NextDate",next_date)
            
            while n < COLS_PER_PAGE:
                date = '%s-%02d' % (year, mon)
                self.ncgi.hdf.setValue("CGI.Months.%d" % n, date)
                self.ncgi.hdf.setValue("CGI.Months.%d.year" % n, str(year))
                self.ncgi.hdf.setValue("CGI.Months.%d.month" % n, str(mon))
                if date == q_date:
                    self.ncgi.hdf.setValue("CGI.Months.%d.hilight" % n, date)
                n += 1
                mon -= 1
                if mon == 0: 
                    mon = 12
                    year -= 1
                if year < fyear: break
                if year == fyear and mon < fmon: break

            # compute "prev >>" nav from vars falling down 
            prev_date = "%s-%02d" % (year,mon)

            log("*** %s = %s" % (prev_date,bymonth.get(prev_date,0)))

            bym_firstnum,bym_count = bym.get(prev_date)
            if bym_count > 0:
                self.ncgi.hdf.setValue("CGI.MonthPage.PrevDate",prev_date)
                
            self.ncgi.hdf.setValue("CGI.TopAuthors", str(n))

    def display_menu(self):
        self.pagename = "menu"
        self.mdb.openByMonth().hdfExport("CGI.ByMonth", self.ncgi.hdf)

    def display_archives(self):
        possible = os.listdir(DISCUSS_DATA_ROOT)
        n = 0
        for file in possible:
            listpath = os.path.join(DISCUSS_DATA_ROOT, file)
            if not os.path.isdir(listpath): continue
            if not os.path.exists("%s/list.hdf" % listpath): continue
            self.ncgi.hdf.setValue("CGI.Archives.%d" % n, file)
            obj = self.ncgi.hdf.getObj("CGI.Archives.%d" % n)
            obj.readFile("%s/list.hdf" % listpath)
            n += 1

    # Used by all feeds (rss91/rss92/rss10/rss20)
    def display_feed(self):
        self.ncgi.hdf.setValue("cgiout.ContentType", "text/xml")
        q_count = self.ncgi.hdf.getIntValue("Query.count", 10)
        if q_count > 100: q_count = 100
        max_doc, max_thread = self.mdb.counts()
        for x in range(q_count):
            try:
                msg = self.mdb.message(max_doc - x, summary = 1)
                msg.hdfExport("CGI.Messages.%d" % x, self.ncgi.hdf, tz=self.tz)
            except message_db.eNoMessage:
                pass

    def display(self):
        if self.pagename == "home":
            self.display_home()
        elif self.pagename == "index":
            self.display_index()
        elif self.pagename == "msg":
            self.display_msg()
        elif self.pagename == "messages":
            self.display_messages()
        elif self.pagename == "threads":
            self.display_threads()
        elif self.pagename == "search":
            self.display_search()
        elif self.pagename == "browse":
            self.display_fullbrowse()
        elif self.pagename == "browse_frm":
            self.display_browse()
        elif self.pagename == "browse_ifrm":
            self.display_browse_ifrm()
        elif self.pagename == "menu":
            self.display_menu()
        elif self.pagename == "top_authors":
            self.display_top_authors()
        elif self.pagename == "archives":
            self.display_archives()
        elif self.pagename == "attach":
            self.display_attachment()
        elif self.pagename in ["rss91", "rss92", "rss10", "rss20"]:
            self.display_feed()
        return

def main(context):
    DiscussPage(context, pagename="discuss").start()

if __name__ == "__main__":
    main(CSPage.Context())

