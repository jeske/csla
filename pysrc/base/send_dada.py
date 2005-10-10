#!/neo/opt/bin/python
"""
  Send Random Test messages

Usage:
send_dada.py [--help] [--lines <num>] [--num <num>] [--fork <num>] dest dada.pb

Where:
  --num <num>       num of messages to send per process
  --fork <num>      num of processes to fork
  dest              destination email address

"""

import whrandom
import os, sys, getopt, time, string


def usage(progname):
  print "usage: %s [--help] [--num <num>] [--fork <num>] dada.pb" % progname
  print __doc__

def main(argc, argv):
  import sendmail

  progname = argv[0]
  alist, args = getopt.getopt(argv[1:], "", ["help", "num=", "fork=", ])

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
    if field == "--num":
      num = int (val)
    if field == "--fork":
      fork = int (val)

  mailto = args[0]
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

    now = time.time()
    def date_header (time_t):
      sec_offset = 0
      tup = time.gmtime(time_t + sec_offset)
      datestr = time.strftime("%a, %d %b %Y %H:%M:%S", tup)
      if sec_offset <= 0: sign = '-'
      else: sign = '+'
      return "%s %s%02d00" % (datestr, sign, abs(sec_offset / 3600))

    date = date_header(now)

    rseed = int(now * 1000 % 10000000)

    cmd = "/usr/local/bin/dada -w 68 -r %d %s" % (rseed, args[1])
    print cmd
    msg = os.popen(cmd, "r").read()
    lines = string.split(msg, '\n')
    email = lines[0]
    lines[0] = "Date: %s" % date
    msg = string.join(lines, '\n')

    print "Message sent to %s from %s\n" % ( mailto, email)
    sendmail.sendmail(email, [mailto], msg)
    #time.sleep(1)


if __name__ == "__main__":
  main(len(sys.argv), sys.argv)

