#! /usr/bin/env python

"""
usage: %(progname)s [args]
"""

import sys, string, os, getopt, pwd, signal, time
import fcntl
import glob

import nstart

from clearsilver import handle_error
from log import *
import re
import message_db
import index

from mimelib import Parser,Message

DISCUSS_DATA_ROOT = "/home/discuss/data"
#DISCUSS_MAILDIR   = "/home/discuss/Maildir"
DISCUSS_MAILDIR   = "/var/lib/mailman/archives/private/*.mbox/*.mbox"

def archive_dirs():
  base_dir = DISCUSS_MAILDIR
  mboxes = glob.glob(base_dir)
  for mboxpath in mboxes:
    _p, fn = os.path.split(mboxpath)
    listname, ext = os.path.splitext(fn)
    
    archive_dir(listname, mboxpath)

def archive_dir(listname, mboxpath):
    # process files...
    global DONE

    listpath = os.path.join(DISCUSS_DATA_ROOT, listname)
    if not os.path.exists(listpath):
      print "list doesn't exists", listpath
      return

    mboxpos_fn = os.path.join(listpath, "mbox.pos")
    if not os.path.exists(mboxpos_fn):
      # create the position file
      open(mboxpos_fn, "w").write('0')
    else:
      if os.stat(mboxpath).st_ctime < os.stat(mboxpos_fn).st_ctime:
        #print "nothing new: ", listname, os.stat(mboxpath).st_ctime, os.stat(mboxpos_fn).st_ctime
        return
    
    pos = int(open(mboxpos_fn, "r").read())

    fp = open(mboxpath, "r")

    index.index_mbox(fp, listname, mboxpath, pos)
        
DONE = 0

def handleSignal(*arg):
    global DONE
    DONE = 1


LockFailed = "LockFailed"

def do_lock(path, filename):
    if not os.path.exists(path):
        os.makedirs(path, 0777)

    lockfp = open(os.path.join(path, filename),"wb")
    try:
	fcntl.lockf(lockfp.fileno(),fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError, reason:
        log ("Unable to lock %s: %s" % (filename, str(reason)))
        raise LockFailed, reason

    lockfp.write("%d" % os.getpid())
    lockfp.truncate()
    return lockfp

def usage(progname):
  print __doc__ % vars()

def main(argv, stdout, environ):
  progname = argv[0]
  optlist, args = getopt.getopt(argv[1:], "", ["help", "test", "debug"])

  testflag = 0
  if len(args) != 0:
    usage(progname)
    return

  lock = do_lock(DISCUSS_DATA_ROOT, "archiver.lock")

  global DONE

  #signal.signal(signal.SIGTERM, handleSignal)

  log("archiver: start")
  try:
    while not DONE:
        try:
            archive_dirs()
        except:
            handle_error.handleException("Archiver Error")
        if DONE: break
        # tlog("sleeping")
        time.sleep(10)
  finally:
    os.unlink(os.path.join(DISCUSS_DATA_ROOT, "archiver.lock"))

if __name__ == "__main__":
  main(sys.argv, sys.stdout, os.environ)
