#! /usr/bin/env python

import os, sys, getopt
import mymailbox

import nstart

from mimelib import Message, Parser
import email_message

from clearsilver.log import *
from clearsilver import handle_error

import message_db

class PosParser(Parser.Parser):
    def pos_parse(self, fp):
        return fp.start, fp.stop, self.parse(fp)

def index_mbox (fp, name, mboxpath, pos=0):
  def raw_message(fp):
    return fp.read()

  mbox = mymailbox.UberUnixMailbox(fp, factory=raw_message)
  mbox.seekp = pos
  listpath = name
  mdb = message_db.MessageDB(listpath)
  mdb.createTables()

  count = 1
  while 1:
    msg = mbox.next()
    if not msg: break
    try:
      mdb.insertMessage(msg)
    except KeyboardInterrupt:
      sys.exit(1)
    except:
      handle_error.handleException("Couldn't handle msg ending at: %s" % (fp.tell()))
    if (count % 8000) == 0:
      log("flushing... (%s)" % count)
      mdb.flush()
      log("done.")
    count = count + 1

  mdb.flush()

  ## write the new position in the mbox
  #pos = fp.tell()
  pos = os.stat(mboxpath).st_size
  mboxpos_fn = os.path.join(listpath, "mbox.pos")
  open(mboxpos_fn, "w").write(str(pos))
  

def usage():
  print "./index.py --name listname (list of mbox files to import)+"

def main(argv):
  alist, args = getopt.getopt(argv[1:], "q:n:", ["help", "name="])

  listname = None
  for (field, val) in alist:
    if field == "--help":
      usage(argv[0])
      return
    if field == "-q":
      query = val
    if field in ['-n', "--name"]:
      listname = val

  if listname is None:
    usage()
    return

  if 1:
    for path in args:
      print "Indexing %s" % path
      fp = open(path, "r")
      index_mbox(fp, listname, path)


if __name__ == "__main__":
  main(sys.argv)
