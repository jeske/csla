#!/neo/opt/bin/python

import sys, string, os, getopt, pwd, signal, time
import fcntl

import nstart

import handle_error
from log import *
import re
import message_db

from mimelib import Parser,Message

DISCUSS_DATA_ROOT = "/home/discuss/data"
DISCUSS_MAILDIR   = "/home/discuss/Maildir"

def archive_dir():

    base_dir = DISCUSS_MAILDIR
    
    new_dir    = os.path.join(base_dir,"new")
    bounce_dir = os.path.join(base_dir,"bounces")
    error_dir  = os.path.join(base_dir,"cur")

    # Always check permissions on directory first!

    # process files...
    global DONE
    
    files = os.listdir(new_dir)
    for a_file in files:
        if DONE: break
        filepath = os.path.join(new_dir,a_file)
        tlog("*** archive message: %s" % filepath)
        try:
            archive_file(filepath)
        except KeyboardInterrupt:
            raise "user keyboard interrupt"
        except:
            log("should move to cur: %s" % filepath)
            handle_error.handleException("on file %s" % filepath)
            try:
                os.link(filepath, os.path.join(error_dir,a_file))
                os.unlink(filepath)
            except OSError:
                pass
    global MDB_CACHE
    for list_path in MDB_CACHE.keys():
        (mdb, counts) = MDB_CACHE[list_path]
        tlog("flushing %s:%d" % (list_path, counts))
        mdb.flush()
    MDB_CACHE = {}

MDB_CACHE = {}

def archive_file(a_file):
    # first out what list this is bound for...
    msg_data = open(a_file).read()

    p = Parser.Parser(Message.Message)
    msgobj = p.parsestr(msg_data)
    frmhdr = msgobj.get("From", "")

    m = re.match("mailman-owner@[^ ]+",frmhdr)
    if m:
        raise "mailman owner email"

    delivered_to = msgobj["Delivered-To"]

    m = re.match("discuss-archiveof-([^ ]+)@neotonic.com",delivered_to)
    if not m:
        raise "didn't match delivered to pattern: %s" % delivered_to

    listname = m.group(1)
    
    list_path = os.path.join(DISCUSS_DATA_ROOT,listname)

    no_archive = msgobj.get("X-No-Archive",None)
    from_request_re_obj = re.match("[^ ]+-request@[^ ]+",frmhdr)

    if no_archive or from_request_re_obj:
        tlog("NO-ARCHIVE [%s] %d bytes / %s / %s" % (listname,len(msg_data),msgobj.get("From","unknown"),msgobj.get("Subject","(no subject)")))
        control_dir = os.path.join(list_path,"control")
        if not os.path.exists(control_dir):
            os.mkdir(control_dir)
        fname = os.path.split(a_file)[-1]
        os.link(a_file,os.path.join(control_dir,fname))
        os.unlink(a_file)
    else:
        # log(listname)
        tlog("[%s] %d bytes / %s / %s" % (listname,len(msg_data),msgobj.get("From","unknown"),msgobj.get("Subject","(no subject)")))

        global MDB_CACHE

        try:
            mdb, counts = MDB_CACHE[list_path]
        except KeyError:
            mdb = message_db.MessageDB(list_path)
            counts = 0

        mdb.insertMessage(msg_data)
        if counts > 1000:
            tlog("flushing %s:%d" % (list_path, counts))
            mdb.flush()
            counts = 0
        MDB_CACHE[list_path] = (mdb, counts+1)
        os.unlink(a_file)
 
        
DONE = 0

def handleSignal(*arg):
    global DONE
    DONE = 1

def usage():
    print "usage info!!"

LockFailed = "LockFailed"

def do_lock(path, filename):
    if not os.path.exists(path):
        os.makedirs(path, 0777)

    lockfp = open("%s/%s" % (path, filename),"wb")
    try:
	fcntl.lockf(lockfp.fileno(),fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError, reason:
        log ("Unable to lock %s: %s" % (filename, str(reason)))
        raise LockFailed, reason

    lockfp.write("%d" % os.getpid())
    lockfp.truncate()
    return lockfp

def main(argv):
    alist, args = getopt.getopt(argv[1:], "", ["help"])

    tup = pwd.getpwnam("discuss")
    DISCUSS_UID = tup[2]

    r_uid = os.getuid()

    if r_uid != DISCUSS_UID:
      if r_uid == 0:
        os.setreuid(DISCUSS_UID, DISCUSS_UID)
      else:
        raise "Most run archiver as discuss!"

    lock = do_lock(DISCUSS_DATA_ROOT, "archiver.lock")

    for (field, val) in alist:
      if field == "--help":
        usage(argv[0])
        return -1

    global DONE

    signal.signal(signal.SIGTERM, handleSignal)

    log("archiver: start")
    while not DONE:
        try:
            archive_dir()
        except KeyboardInterrupt:
            DONE = 1
        except:
            import handle_error
            handle_error.handleException("Archiver Error")
        if DONE: break
	# tlog("sleeping")
        time.sleep(10)

if __name__ == "__main__":
  main(sys.argv)
