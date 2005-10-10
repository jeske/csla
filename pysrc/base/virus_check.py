
import time, os, socket, re, string
from log import log

_COUNT = 0

class VirusChecker:
    def __init__ (self):
        self._scanners = []

    def pushScanner(self, scanner):
        self._scanners.append(scanner)

    def check_email_message(self, data):
        for scanner in self._scanners:
            found = scanner.scan_email(data)
            if found: return found

    def check_file(self, filename):
        for scanner in self._scanners:
            found = scanner.scan_file(filename)
            if found: return found

    def check_directory(self, dirname):
        pass


class McAffeVirusScan:
    def __init__ (self):
        self._uvscan = "/neo/opt/uvscan/uvscan"
        self._datdir = "/neo/data/mcaffe-dat"
        self._tmpdir = "/tmp"
        self._found_re = re.compile("Found the ([^ ]+) virus")
        self._found2_re = re.compile("Found: ([^ ]+)")

    def tempfile(self):
        global _COUNT
        r = _COUNT
        _COUNT = _COUNT + 1
        fn = "vs.%d.%s_%s.%s" % (int(time.time()), os.getpid(), r, socket.gethostname())
        path = os.path.join(self._tmpdir, fn)
        return path

    def scan_email(self, data):
        tname = self.tempfile()
        open(tname, 'w').write(data)
        try:
            ret = self.scan_file(tname)
        finally:
            os.unlink(tname)
        return ret

    def scan_file(self, filename):
        cmd = "%s --mime --noboot --noexpire --unzip --dat %s %s" % (self._uvscan, self._datdir, filename)
        fp = os.popen(cmd, 'r')
        ret = fp.readlines()
        status = fp.close()
        if status is None: return ""
        if type(status) == type(1) and os.WIFEXITED(status):
            code = os.WEXITSTATUS(status)
            if code == 0: return ""
            if code == 13: 
                what = ret[1]
                m = self._found_re.search(what)
                if m is None:
                    m = self._found2_re.search(what)
                if m:
                    what = m.group(1)
                return string.strip(what)
            log("Unknown exit code returned by uvscan: %d" % status)
        else:
            log("Weird exit status for uvscan: %s" % repr(status))
        # default is to return no problem
        return ""
