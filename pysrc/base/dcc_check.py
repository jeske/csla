
import os, popen2
from log import log

eDCCerror = "eDCCerror"

def dcc_check_message(data, report=1):
    if not os.path.exists("/usr/local/bin/dccproc"):
        return ""
    if report:
        cmd = "/usr/local/bin/dccproc -H"
    else:
        cmd = "/usr/local/bin/dccproc -H -Q"
    pop = popen2.Popen3(cmd, 1)
    pop.tochild.write(data)
    pop.tochild.close()
    output = pop.fromchild.read()
    error = pop.childerr.read()
    status = pop.wait()
    if error:
        raise eDCCerror, error
    output = output.strip()
    if output:
        x = output.find(':')
        if x != -1:
            return output[x+1:].strip()
        return output
    if not status: return ""
    if type(status) == type(1):
        if os.WIFEXITED(status):
            if os.WEXITSTATUS(status):
                raise eDCCerror, "dccproc returned %d" % (os.WEXITSTATUS(status))
        elif os.WIFSIGNALED(status):
            raise eDCCerror, "dccproc ended on signal %d" % (os.WTERMSIG(status))
        elif os.WIFSTOPPED(status):
            raise eDCCerror, "dccproc ended on signal %d" % (os.WSTOPSIG(status))
    return ""
    
