

import os, sys, string, re, time
import marshal

from TCS.bsddb import db
import neo_cgi, neo_util
from log import *

eNotCached = "eNotCached"

class MessageCache:
    def __init__ (self, path):
        self._path = path
#        try:
#            db.appinit(path, db.DB_INIT_LOCK | db.DB_CREATE)
#        except:
#            raise "failure opening DB Env at: %s" % path
        dbf = db.DB()
        if not os.path.exists(self._path + '/cache'):
            os.makedirs(self._path + '/cache', 0777)
        path = "%s/cache/messages.db" % self._path
        try:
            dbf.open(path, db.DB_BTREE, db.DB_CREATE)
        except:
            raise "failure opening message cache: %s" % path
        self._db = dbf

    def get(self, doc_id, prefix, hdf):
        try:
            data = self._db.get(str(doc_id))
        except db.error, reason:
            if reason[0] == -7:
                raise eNotCached
            log("bad message cache for %d" % doc_id)
            import handle_error
            handle_error.handleException("bad cache")
            raise eNotCached

        hdf.setValue(prefix, "1")
        obj = hdf.getObj(prefix)
        try:
            obj.readString(data)
        except:
            log("bad message cache for %d" % doc_id)
            import handle_error
            handle_error.handleException("bad cache")
            raise eNotCached

    def store(self, doc_id, prefix, hdf):
        obj = hdf.getObj(prefix)
        s = obj.writeString()
        self._db.put(str(doc_id), s)

class IndexCache:
    def __init__ (self, path):
        self._path = path
        if not os.path.exists(self._path + '/cache'):
            os.makedirs(self._path + '/cache', 0777)

    def get(self, month, prefix, hdf,inv_key=None):
        path = os.path.join(self._path, "cache", "idx_%s.hdf" % month)
        if not os.path.exists(path):
            raise eNotCached

        cache_hdf = neo_util.HDF()
        try:
            cache_hdf.readFile(path)
        except:
            import handle_error
            handle_error.handleException("bad index cache: %s" % path)
            raise eNotCached

            
        if inv_key:
            if cache_hdf.getValue("cacheinfo.inv_key","") != inv_key:
                log("cache invalidation (%s,%s!=%s)!" % (month,inv_key,cache_hdf.getValue("cacheinfo.inv_key","")))
                raise eNotCached

        hdf.setValue(prefix, "1")
        hdf.copy(prefix,cache_hdf.getObj("cachedata"))
              
    def nuke(self, month):
        path = os.path.join(self._path, "cache", "idx_%s.hdf" % month)
        os.unlink(path)

    def store(self, month, prefix, hdf,inv_key=None):
        path = os.path.join(self._path, "cache", "idx_%s.hdf" % month)
        obj = hdf.getObj(prefix)

        if obj is None: return

        cache_hdf = neo_util.HDF()
        if inv_key:
            cache_hdf.setValue("cacheinfo.inv_key",str(inv_key))
        cache_hdf.copy("cachedata",obj)
            
        cache_hdf.writeFileAtomic(path)


