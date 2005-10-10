
import os, sys, string, time, getopt, socket
from log import *

InvalidQueue = "Invalid Queue"

class MaildirQueue:
  _COUNT = 1
  def __init__(self, path, subqueues=[]):
    if path[-1] == '/': path = path[:-1]
    if type(subqueues) == type([]):
      self._subqueues = ["new", "cur", "tmp"] + subqueues
    elif type(subqueues) == type(""):
      if subqueue not in self._subqueues:
        self._subqueues.append(subqueue)
    self.path_(path)
    oum = os.umask(0)

  def path_(self, path): 
    if path[0] != "/":
      raise InvalidQueue, "%s is not a full path" % path
    if not os.path.exists(path):
      os.makedirs(path, 0777)
    self._path = path; 
    self._listdircache = {}
    try:
      files = os.listdir(path)
    except os.error, reason:
      files = []

    ## find all subqueues
    for file in files:
      rfn = os.path.join(path, file)
      if os.path.isdir(rfn):
        if rfn not in self._subqueues:
          self._subqueues.append(rfn)

    self._checkqueues()
    return self

  def reload(self):
    self._listdircache = {}

  def _checkqueue(self, subqueue):
    path = os.path.join(self._path, subqueue)
    if not os.path.isdir(path): 
      log("creating '%s'" % path)
      os.mkdir(path, 0775)
    
  def _checkqueues(self):
    for subqueue in [""] + self._subqueues:
      self._checkqueue(subqueue)

  def addsubqueue(self, subqueue):
    if subqueue[0] == "/":
      raise InvalidQueue, "%s is a full path, not a subqueue" % subqueue
    if subqueue not in self._subqueues:
      self._subqueues.append(subqueue)
      self._checkqueue(subqueue)

  def _isvalidqueue(self, subqueue):
    if subqueue not in self._subqueues:
      raise InvalidQueue, "no such subqueue %s, use MaildirQueue.addsubqueue(subqueue)" % subqueue
    return 1

  def tmpfile(self):
    r = MaildirQueue._COUNT
    MaildirQueue._COUNT = MaildirQueue._COUNT + 1
    fn = "%d.%s_%s.%s" % (int(time.time()), os.getpid(), r, socket.gethostname())
    path = os.path.join(self._path, "tmp", fn)
    return path

  def enqueue(self, file, subqueue):
    self._isvalidqueue(subqueue)
    fn = file
    if fn[0] != "/":
      raise InvalidQueue, "%s: not a full path" % fn

    path, filename = os.path.split(fn)
    
    newfilename = os.path.join(self._path, subqueue, filename)

    try:
      os.link(fn, newfilename)
    except os.error, reason: 
      os.unlink(newfilename)
      log("%s %s %s %s" % (os.error, reason, fn, newfilename))
      return ""

    try:
      os.unlink(fn)
    except os.error, reason:
      os.unlink(newfilename)
      log("%s %s %s %s" % (os.error, reason, fn, newfilename))
      return ""

    self._invalidatequeue(subqueue)
    return newfilename
        
  def _invalidatequeue(self, subqueue):
    try:
      del self._listdircache[subqueue]
    except KeyError:
      pass

  def _listdir(self, subqueue):
    d = self._listdircache.get(subqueue, None)

    if d is None or len(d) == 0:
      d = os.listdir(os.path.join(self._path, subqueue))
      d.sort()

    if len(d) == 0:
      d = None
      try:
	del self._listdircache[subqueue]
      except KeyError:
	pass
    else:
      self._listdircache[subqueue] = d
    return d

  def queuelength(self, subqueue):
    self._isvalidqueue(subqueue)
    ld = self._listdir(subqueue)
    if ld is None: return 0
    return len(ld)
    
  ## returns None if there are no more entries      
  def dequeue(self, subqueue):
    self._isvalidqueue(subqueue)

    ld = self._listdir(subqueue)
    if ld is None:
      return None
    fn = os.path.join(self._path, subqueue, ld[0])
    del ld[0]

    return fn

  def remove(self, fn):
    path, filename = os.path.split(fn)
    ppath, subqueue = os.path.split(path)
    if ppath != self._path:
      log ("Cannot remove file %s, wrong Maildir" % fn)
      return

    self._isvalidqueue(subqueue)

    try:
      os.unlink(fn)
    except OSError, reason:
      if reason[0] != 2:
        raise
    ld = self._listdir(subqueue)
    if ld is None: return
    try:
      ld.remove(filename)
    except ValueError:
      pass
