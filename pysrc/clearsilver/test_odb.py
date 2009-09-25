#! /usr/bin/env python

"""
usage: %(progname)s [args]
"""

import os, sys, string, time, getopt
from log import *

import odb


## -----------------------------------------------------------------------
##                            T  E  S  T S
## -----------------------------------------------------------------------

        
def TEST_MYSQL(output=warn):
    output("------ TESTING MySQLdb ---------")

    import odb_mysql
    conn = odb_mysql.Connection(host = 'localhost',user='root', passwd = '', db='test')
    db = odb.Database(conn)

    TEST_DATABASE(db,output=output)



def TEST_SQLITE(output=warn):
    output("------ TESTING sqlite2 ----------")

    import odb_sqlite
    conn = odb_sqlite.Connection("/tmp/test2.db", autocommit=1)
    db = odb.Database(conn)

    TEST_DATABASE(db,output=output)

def TEST_SQLITE3(output=warn):
    output("------ TESTING sqlite3 ----------")

    import odb_sqlite3
    conn = odb_sqlite3.Connection("/tmp/test3.db", autocommit=1)
    db = odb.Database(conn)

    TEST_DATABASE(db,output=output)

def TEST_POSTGRES(output=warn):
    output("------ TESTING postgres ----------")

    import odb_postgres
    conn = odb_postgres.Connection(database="test")
    db = odb.Database(conn)

    TEST_DATABASE(db,output=output)
    
    


def TEST_DATABASE(db, output=log):

    class AgentsTable(odb.Table):
        def _defineRows(self):
            self.d_addColumn("agent_id",odb.kInteger,None,primarykey = 1,autoincrement = 1)
            self.d_addColumn("login",odb.kVarString,200,notnull=1)
            self.d_addColumn("ext_email",odb.kVarString,200,notnull=1, indexed=1)
            self.d_addColumn("hashed_pw",odb.kVarString,20,notnull=1)
            self.d_addColumn("name",odb.kBigString,compress_ok=1)
            self.d_addColumn("auth_level",odb.kInteger,None)
            self.d_addColumn("ticket_count",odb.kIncInteger,None)
            self.d_addColumn("data",odb.kBlob,None, compress_ok=1)
            self.d_addValueColumn()
            self.d_addVColumn("columnA",odb.kInteger,None)

    class TestTable(odb.Table):
        def _defineRows(self):
            self.d_addColumn("oid",odb.kInteger,None,primarykey = 1,autoincrement = 1)
            self.d_addColumn("a",odb.kInteger, primarykey = 1)
            self.d_addColumn("b",odb.kInteger)
            

    db.enabledCompression()

    db.addTable("agents", "agents", AgentsTable)
    try: db.agents.dropTable()
    except: pass

    db.addTable("test", "test", TestTable)
    try: db.test.dropTable()
    except: pass
    
    db.createTables()
    db.createIndices()

    tbl = db.agents

    TEST_INSERT_COUNT = 5

    # ---------------------------------------------------------------
    # make sure we can catch a missing row

    try:
        a_row = tbl.fetchRow( ("agent_id", 1000) )
        raise "test error"
    except odb.eNoMatchingRows:
        pass

    output("PASSED! fetch missing row test")

    # --------------------------------------------------------------
    # create new rows and insert them

    for n in range(TEST_INSERT_COUNT):
        new_id = n + 1
        
        newrow = tbl.newRow()
        newrow.name = "name #%d" % new_id
        newrow.login = "name%d" % new_id
        newrow.ext_email = "%d@name" % new_id
        newrow.hashed_pw = "hashedpw"
        newrow.save()
        if newrow.agent_id != new_id:
            raise "new insert id (%s) does not match expected value (%d)" % (newrow.agent_id,new_id)

    output("PASSED! autoinsert test")

    # --------------------------------------------------------------
    # fetch one row
    a_row = tbl.fetchRow( ("agent_id", 1) )

    if a_row.name != "name #1":
        raise "row data incorrect"

    output("PASSED! fetch one row test")

    # ---------------------------------------------------------------
    # don't change and save it
    # (i.e. the "dummy cursor" string should never be called!)
    #
    try:
        a_row.save(cursor = "dummy cursor")
    except AttributeError, reason:
        raise "row tried to access cursor on save() when no changes were made!"

    output("PASSED! don't save when there are no changed")

    # ---------------------------------------------------------------
    # change, save, load, test
    
    a_row.auth_level = 10
    a_row.save()
    b_row = tbl.fetchRow( ("agent_id", 1) )
    if b_row.auth_level != 10:
        log(repr(b_row))
        raise "save and load failed"
    

    output("PASSED! change, save, load")

    # ---------------------------------------------------------------
    # replace

    if 0:
      repl_row = tbl.newRow(replace=1)
      repl_row.agent_id = a_row.agent_id
      repl_row.login = a_row.login + "-" + a_row.login
      repl_row.ext_email = "foo"
      repl_row.hashed_pw = "hashed_pw"
      repl_row.save()

      b_row = tbl.fetchRow( ("agent_id", a_row.agent_id) )
      if b_row.login != repl_row.login:
          raise "replace failed"
      output("PASSED! replace")

    # --------------------------------------------------------------
    # access unknown attribute
    try:
        a = a_row.UNKNOWN_ATTRIBUTE
        raise "test error"
    except AttributeError, reason:
        pass
    except odb.eNoSuchColumn, reason:
        pass

    try:
        a_row.UNKNOWN_ATTRIBUTE = 1
        raise "test error"
    except AttributeError, reason:
        pass
    except odb.eNoSuchColumn, reason:
        pass

    output("PASSED! unknown attribute exception")

    # --------------------------------------------------------------
    # access unknown dict item

    try:
        a = a_row["UNKNOWN_ATTRIBUTE"]
        raise "test error"
    except KeyError, reason:
        pass
    except odb.eNoSuchColumn, reason:
        pass

    try:
        a_row["UNKNOWN_ATTRIBUTE"] = 1
        raise "test error"
    except KeyError, reason:
        pass
    except odb.eNoSuchColumn, reason:
        pass

    output("PASSED! unknown dict item exception")

    # --------------------------------------------------------------
    # use wrong data for column type

    if 0:
      try:
          a_row.agent_id = "this is a string"
          raise "test error"
      except eInvalidData, reason:
          pass

      output("PASSED! invalid data for column type")

    # --------------------------------------------------------------
    # fetch 1 rows

    rows = tbl.fetchRows( ('agent_id', 1) )
    if len(rows) != 1:
        raise "fetchRows() did not return 1 row!" % (TEST_INSERT_COUNT)

    output("PASSED! fetch one row")


    # --------------------------------------------------------------
    # fetch All rows
    
    rows = tbl.fetchAllRows()
    if len(rows) != TEST_INSERT_COUNT:
        for a_row in rows:
            output(repr(a_row))
        raise "fetchAllRows() did not return TEST_INSERT_COUNT(%d) rows!" % (TEST_INSERT_COUNT)

    output("PASSED! fetchall rows")

  


    # --------------------------------------------------------------
    # delete row object

    row = tbl.fetchRow( ('agent_id', 1) )
    row.delete()
    try:
        row = tbl.fetchRow( ('agent_id', 1) )
        raise "delete failed to delete row!"
    except odb.eNoMatchingRows:
        pass

    # --------------------------------------------------------------
    # table deleteRow() call

    row = tbl.fetchRow( ('agent_id',2) )
    tbl.deleteRow( ('agent_id', 2) )
    try:
        row = tbl.fetchRow( ('agent_id',2) )
        raise "table delete failed"
    except odb.eNoMatchingRows:
        pass

    # --------------------------------------------------------------

    row = tbl.fetchRow( ('agent_id',3) )
    if row.databaseSizeForColumn('name') != len(row.name):
        raise "databaseSizeForColumn('name') failed"

    # --------------------------------------------------------------
    # table fetchRowUsingPrimaryKey

    row = tbl.fetchRowUsingPrimaryKey(3)
    if row.agent_id != 3:
      raise "fetchRowUsingPrimaryKey failed"

    row = tbl.lookup(agent_id=3)
    if row.agent_id != 3:
      raise "lookup failed"

    row = tbl.lookupCreate(agent_id=2)
    if row.isClean():
      raise "lookup/create failed"
    row.login = 1
    row.ext_email = "hassan@dotfunk.com"
    row.hashed_pw = "sdfj"
    row.save()

    if 0:
      # --------------------------------------------------------------
      # test inc fields
      row = tbl.newRow()
      new_id = 1092
      row.name = "name #%d" % new_id
      row.login = "name%d" % new_id
      row.ext_email = "%d@name" % new_id
      row.inc('ticket_count')
      row.hashed_pw = "hashed_pw"
      row.save()
      new_id = row.agent_id

      trow = tbl.fetchRow( ('agent_id',new_id) )
      if trow.ticket_count != 1:
          raise "ticket_count didn't inc!", repr(trow.ticket_count)

      row.inc('ticket_count', count=2)
      row.save()
      trow = tbl.fetchRow( ('agent_id',new_id) )
      if trow.ticket_count != 3:
          raise "ticket_count wrong, expected 3, got %d" % trow.ticket_count

      trow.inc('ticket_count')
      trow.save()
      if trow.ticket_count != 4:
          raise "ticket_count wrong, expected 4, got %d" % trow.ticket_count


    if 1:
      try:
        b_row = tbl.fetchRow( ("agent_id", 5) )
      except odb.eNoMatchingRows:
        raise "test error"

      b_row.columnA = "hello"
      b_row.save()

      b_row = tbl.fetchRow( ("agent_id", 5) )
      if b_row.columnA != "hello":
        raise "test error", b_row.columnA

      output("PASSED! virtual column test")

    if 1:
      try:
        b_row = tbl.fetchRow( ("agent_id", 5) )
      except odb.eNoMatchingRows:
        raise "test error"

      d = "hello\0hello" * 100
      b_row.data = d
      b_row.save()

      b_row = tbl.fetchRow( ("agent_id", 5) )
      if b_row.data != d:
        raise "test error", repr(b_row.data)

      output("PASSED! blob column test")
      
      
    output("\n==== ALL TESTS PASSED ====")



def test():
  pass

def usage(progname):
  print __doc__ % vars()

def main(argv, stdout, environ):
  progname = argv[0]
  optlist, args = getopt.getopt(argv[1:], "", ["help", "test", "debug"])

  testflag = 0

  for (field, val) in optlist:
    if field == "--help":
      usage(progname)
      return
    elif field == "--debug":
      debugfull()
    elif field == "--test":
      testflag = 1

  if testflag:
    test()
    return

  for arg in args:
    if arg == "sqlite2":
      TEST_SQLITE()
    elif arg == "sqlite3":
      TEST_SQLITE3()
    elif arg == "mysql":
      TEST_MYSQL()
    elif arg == "postgres":
      TEST_POSTGRES()

if __name__ == "__main__":
  main(sys.argv, sys.stdout, os.environ)
