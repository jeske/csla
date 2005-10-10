#!/neo/opt/bin/python
"""
  Send Random Test messages

Usage:
RandomWords.py [--help] [--lines <num>] [--num <num>] [--fork <num>] dest [from] [from name]

Where:
  --lines <num>     num of lines per message
  --num <num>       num of messages to send per process
  --fork <num>      num of processes to fork
  dest              destination email address
  from              email envelope from address

"""

import whrandom
import os, sys, getopt, time

gDict = "/usr/dict/words";
gWords = None

class RandomWords:
  def __init__ (self):
    global gWords
    if not gWords:
      fp = open (gDict)
      gWords = fp.readlines()
      fp.close()
    self._words = gWords

  def word (self):
    word = whrandom.choice(self._words)
    if word[-1] == "\n":
      word = word[:-1]
    return word
    
  def words (self, number):
    words = self.word()
    for x in range (number-1):
      words = words + " " + self.word()
    return words

  def message (self, maxlines = 1000, max = None):
    if not max:
      max = whrandom.randint(100, 5000)
    slen = 0
    lines = 0

    results = ""
    
    for x in range (max):
      word = self.word()
      if (len (word) + slen) > 72:
        lines = lines + 1
        if (lines > maxlines):
          return results
        results = results + "\n"
        slen = 0

      slen = slen + len (word)
      results = results + word + " "

    return results

    

def usage(progname):
  print "usage: %s [--help] [--lines <num>] [--num <num>] [--fork <num>]" % progname
  print __doc__

def main(argc, argv):
  import sendmail

  progname = argv[0]
  alist, args = getopt.getopt(argv[1:], "", ["help", "lines=", "num=", "fork=", ])

  maxlines = 100
  num = 1
  fork = 0
  random_from = 1

  if len (args) < 1:
    usage (progname)
    return

  for (field, val) in alist:
    if field == "--help":
      usage(progname)
      return
    if field == "--lines":
      maxlines = int(val)
    if field == "--num":
      num = int (val)
    if field == "--fork":
      fork = int (val)

  mailto = args[0]
  email = ""
  author = "RandomWords"
  if len (args) > 1:
    email = args[1]
    random_from = 0
  if len (args) > 2:
    author = args[2]

  print "Creating %d processes" % fork
  while (fork):
    pid = os.fork()
    if pid == 0:
      # In child
      whrandom.seed (int(time.time()) % 256, fork % 256, os.getpid() % 256)
      fork = 0
      print "Created Child Process"
    else:
      # In parent
      fork = fork - 1

  for x in range (num):
    rw = RandomWords()

    body = rw.message(maxlines)
    body = body + "\n-- \n  This is a test message!\n"

    subject = rw.words(5)

    now = time.time()
    def date_header (time_t):
      sec_offset = 0
      tup = time.gmtime(time_t + sec_offset)
      datestr = time.strftime("%a, %d %b %Y %H:%M:%S", tup)
      if sec_offset <= 0: sign = '-'
      else: sign = '+'
      return "%s %s%02d00" % (datestr, sign, abs(sec_offset / 3600))

    date = date_header(now)

    if random_from:
        first_name = rw.word()
        last_name = rw.word()
        email = 'blong-%s@fiction.net' % last_name
        author = "%s %s" % (first_name, last_name)

    print "Message sent to %s from \"%s\" <%s>\n  Subject: %s" % ( mailto, author, email, subject)
    msg = 'To: %s\nFrom: "%s" <%s>\nSubject: %s\nDate: %s\n\n%s' % (mailto, author, email, subject, date, body)
    sendmail.sendmail(email, [mailto], msg)


if __name__ == "__main__":
  main(len(sys.argv), sys.argv)

