#!/neo/opt/bin/python

import sys, getopt
import mymailbox

import nstart

from mimelib import Message, Parser
import email_message

from log import *

import message_db
import handle_error

class PosParser(Parser.Parser):
    def pos_parse(self, fp):
        return fp.start, fp.stop, self.parse(fp)

def index_mbox (path, name):
  fp = open(path)

  def raw_mesasge(fp):
    return fp.read()

  mbox = mymailbox.UberUnixMailbox(fp, factory=raw_mesasge)
  mdb = message_db.MessageDB("/home/discuss/data/%s" % name)
  count = 0
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

def usage():
  print "./index.py --name listname (list of files)+"

def main(argv):
  alist, args = getopt.getopt(argv[1:], "q:n:", ["help", "name="])

  query = None
  name = None
  for (field, val) in alist:
    if field == "--help":
      usage(argv[0])
      return
    if field == "-q":
      query = val
    if field in ['-n', "--name"]:
      name = val

  if name is None:
    usage()
    return

  if query:
    rtv = neo_rtv.Retrieve("mail/")
    results = rtv.search(query)
    print "There were %d matches" % len(results)
    for doc in results:
      print "Document %s" % doc
  else:
    for path in args:
      print "Indexing %s" % path
      index_mbox(path, name)

if __name__ == "__main__":
  main(sys.argv)
