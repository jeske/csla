
import os, sys, string, re, time
import marshal

from log import *

import time,hashlib

import neo_cgi, neo_util

from clearsilver import odb, hdfhelp, odb_sqlite3

class WhichReadDB(odb.Database):
  def __init__ (self, conn):
    odb.Database.__init__(self, conn)
    self.addTable("whichread",  "wr_whichread",  WhichReadTable)

  def get(self, readerid):
    row = self.whichread.lookup(readerid=readerid)
    if not row: row = ''
    return row

class WhichReadTable(odb.Table):
  def _defineRows(self):
    self.d_addColumn("readerid", odb.kVarString, primarykey=1)
    self.d_addColumn("wrlist", odb.kVarString)

def createTables(path):
  dbpath = "%s/whichread.db3" % path
#  conn = odb_sqlite3.Connection(dbpath, autocommit=0)
  conn = odb_sqlite3.Connection(dbpath)
  db = WhichReadDB(conn)

  db.createTables()
  db.synchronizeSchema()
  db.createIndices()

  

class WhichRead:
    def __init__ (self, listname,path,ncgi):
        self.listname = listname
        self._path = path
        self.ncgi = ncgi
        self.__db = None
        self._whichReadID = self.getWhichReadID()

    def getWhichReadID(self):
        wrid = self.ncgi.hdf.getValue("Cookie.WRID","")
        if not wrid:
           m = hashlib.md5()
           m.update("%s-%s" % (self.ncgi.hdf.getValue("CGI.RemoteAddress","ADDR"),
                               time.time()))
           wrid = m.hexdigest()
           log("issued new WhichReadID: %s" % wrid)
           self.ncgi.cookieSet("WRID",wrid,persist=1)
           # self.ncgi.hdf.setValue("Cookie.WRID",wrid)
        return wrid

    def _db(self):
        if self.__db is None:
            dbpath = "%s/whichread.db3" % self._path
#            conn = odb_sqlite3.Connection(dbpath, autocommit=0)
            conn = odb_sqlite3.Connection(dbpath)
            self.__db = WhichReadDB(conn)
        return self.__db

    def markMsgRead(self, message_num):

        # unpack the seen cookie
        seencookiename = "%s.WR" % self.listname
        seencookie = self.ncgi.hdf.getValue("Cookie.%s" % seencookiename, "")
        if seencookie:
          c_parts = string.split(seencookie,",")
        else:
          c_parts = []
        mnum_str = "%s" % message_num

        try:
          index = c_parts.remove(mnum_str)
          log("already seen in cookie: %s" % message_num)
        except ValueError:
          log("markread: %s" % message_num)
          # yes, it's new!
          
          # make a new seen cookie! (only 200 entries)
          c_parts.insert(0,mnum_str)
          new_seencookie = string.join(c_parts[:200],",")
          self.ncgi.cookieSet(seencookiename,new_seencookie,persist=1)

          # add to whichread DB
          self.addToDB(message_num)

          # append to whichread log
          fp = open("%s/whichreadchanges.log" % self._path,"ab+")
          fp.write("%s %s\n" % (self._whichReadID,mnum_str))
          fp.close()

    def getWRList(self):
        # read whichread from disk
        wdb = self._db()
        whichread = ""

        whichread = wdb.whichread.lookup(readerid=self._whichReadID)
        if whichread is None:
          wrlist = ''
        else:
          wrlist = whichread.wrlist
        wrl = WRList(wrlist)
        return wrl

    def addToDB(self,mnum):
        wdb = self._db()
        whichread = ""
        
        whichread = wdb.whichread.lookup(readerid=self._whichReadID)
        if whichread is None:
          wrlist = ''
        else:
          wrlist = whichread.wrlist

        wr_list = WRList(wrlist)
        wr_list.markRead(mnum)
        
        row = wdb.whichread.lookupCreate(readerid=self._whichReadID)
        row.wrlist = wr_list.dump()
        row.save()

    def __del__ (self):
        if self.__db:
            self.__db.close()


class WRList:
    def __init__(self,val):
        self._val = val
        self._parts = string.split(val,",")
        self._dict = {}
        dict = self._dict
        for a_part in self._parts:
            dict[a_part] = 1

    def markRead(self,mnum):
        mnum = "%s" % mnum
        try:
            index = self._parts.index(mnum)
        except ValueError:
            self._parts.insert(0,mnum)
        
    def dump(self):
        # log("WRLIST: %s" % self._parts)
        return string.join(self._parts,",")

    def isRead(self,mnum):
        mnum = "%s" % mnum
        # log("isRead %s = %s" % (mnum,self._dict.has_key(mnum)))
        return self._dict.has_key(mnum)
            
