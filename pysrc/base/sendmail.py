#/usr/local/bin/python

# sendmail.py
#
# a simple interface for injecting mail to the local mail delivery
# agent
#

import os,string,re
import MaildirQueue
import log

DISABLED=0

def delayed_queue(BOUNCE_RETURN_ADDRESS, TO_ADDRESS_LIST, BODY):
    mq = MaildirQueue.MaildirQueue("/neo/data/queue")
    fn = mq.tmpfile()
    fp = open(fn, "w")
    fp.write("%s\n-##SEP##-\n" % BOUNCE_RETURN_ADDRESS)
    fp.write("%s\n-##SEP##-\n" % string.join(TO_ADDRESS_LIST, "\n"))
    fp.write(BODY)
    fp.close()
    mq.enqueue(fn, "new")

VALID_CHARS = string.ascii_letters + string.digits + "@.+-_,:"
VALID_CHARS_RE = "([^-@\+\._,:A-Za-z0-9])"

def shell_escape(s):
    global VALID_CHARS, VALID_CHARS_RE
    # This should work.. but it doesn't
    #invalid_re = re.compile(VALID_CHARS_RE)
    #return invalid_re.sub(r'\\1', s)

    o = []
    for x in range(len(s)):
        if s[x] not in VALID_CHARS:
            o.append("\\%s" % s[x])
        else:
            o.append(s[x])
    return ''.join(o)


def sendmail(BOUNCE_RETURN_ADDRESS,TO_ADDRESS_LIST,BODY):
    global DISABLED
    if DISABLED:
        log ("Not sending to %s" % repr(TO_ADDRESS_LIST))
        return
    try:
        mod_to_list = []
        for address in TO_ADDRESS_LIST:
            mod_to_list.append(shell_escape(address))
            
        cmd = "/usr/lib/sendmail -oi -f'%s' -- %s" % (BOUNCE_RETURN_ADDRESS,
                                            string.join(mod_to_list, ' '))
        fp = os.popen(cmd, "w", 16384)
        fp.write(BODY)
        r = fp.close()
        if not r: return
        if os.WIFEXITED(r):
            if os.WEXITSTATUS(r):
                raise "cmd '%s' returned %d" % (cmd, os.WEXITSTATUS(r))
        elif os.WIFSIGNALED(r):
            raise "cmd '%s' ended on signal %d" % (cmd, os.WTERMSIG(r))
        elif os.WIFSTOPPED(r):
            raise "cmd '%s' ended on signal %d" % (cmd, os.WSTOPSIG(r))
    except IOError:
        delayed_queue(BOUNCE_RETURN_ADDRESS, TO_ADDRESS_LIST, BODY)
    except:
        import handle_error
        handle_error.handleException("Unable to send message")
        delayed_queue(BOUNCE_RETURN_ADDRESS, TO_ADDRESS_LIST, BODY)
