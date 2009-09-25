#!/usr/bin/env python

import neo_cgi, neo_cs
import sys, os, string
import time
from log import *

# errors thrown...
NoPageName = "NoPageName"
NoDisplayMethod = "NoDisplayMethod"

# errors signaled back to here
Redirected = "Redirected"
DisplayDone = "DisplayDone"
DisplayError = "DisplayError"

class Context:
    def __init__ (self):
        self.argv = sys.argv
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.environ = os.environ

class CSPage:
    def __init__(self, context, pagename=0,readDefaultHDF=1,israwpage=0,**parms):
        if pagename == 0:
            raise NoPageName, "missing pagename"
        self.pagename = pagename
        self.readDefaultHDF = readDefaultHDF
        self._israwpage = israwpage
        self.context = context
        self._pageparms = parms

        self._error_template = None

        self.page_start_time = time.time()
        neo_cgi.cgiWrap(context.stdin, context.stdout, context.environ)
        neo_cgi.IgnoreEmptyFormVars(1)
        self.ncgi = neo_cgi.CGI()
        self.ncgi.parse()
        self._path_num = 0
        domain = self.ncgi.hdf.getValue("CGI.ServerName","")
        domain = self.ncgi.hdf.getValue("HTTP.Host", domain)
        self.domain = domain
        self.subclassinit()
        self.setPaths([self.ncgi.hdf.getValue("CGI.DocumentRoot","")])

        self._sent_headers = 0
        self._reply_headers = {}
        self._reply_code = 200

        if self.ncgi.hdf.getValue("CGI.HTTPS", ""):
          self.http = "https://"
        else:
          self.http = "http://"

    def __setitem__(self, key, value):
      self._reply_headers[string.lower(key)] = value
      self.ncgi.hdf.setValue("cgiout.other.%s" % key, "%s: %s" % (key, value))

    def __getitem__(self, key):
      return self._reply_headers[string.lower(key)]

    def has_key(self, key):
      return self._reply_headers.has_key(string.lower(key))

    def subclassinit(self):
        pass

    def setPaths(self, paths):
        for path in paths:  
            self.ncgi.hdf.setValue("hdf.loadpaths.%d" % self._path_num, path)
            self._path_num = self._path_num + 1
            
    def redirectUri(self,redirectTo):
        ncgi = self.ncgi
        if ncgi.hdf.getIntValue("Cookie.debug",0) == 1:
            ncgi.hdf.setValue("CGI.REDIRECT_TO",redirectTo)
#            ncgi.display("dbg/redirect.cs")

            cs = neo_cs.CS(ncgi.hdf)
            self['Content-Type'] = "text/html"
            template = """
Redirect
<br><br>
<a href="<?cs var:CGI.REDIRECT_TO ?>"><?cs var:CGI.REDIRECT_TO ?></a>
"""
            cs.parseStr(template)
            page = cs.render()

            self.push(page)

            self.push("<PRE>\n")
            self.push(neo_cgi.htmlEscape(ncgi.hdf.dump()) + "\n")
            self.push("</PRE>\n")
            raise DisplayDone

        self.ncgi.redirectUri(redirectTo)
        raise Redirected, "redirected To: %s" % redirectTo

    ## ----------------------------------
    ## methods to be overridden in subclass when necessary:

    def setup(self):
        pass

    def display(self):
        raise NoDisplayMethod, "no display method present in %s" % repr(self)

    def main(self):
        self.setup()
        self.handle_actions()
        self.display()

    ## ----------------------------------
        
    def handle_actions(self):
        hdf = self.ncgi.hdf
        hdfobj = hdf.getObj("Query.Action")
        if hdfobj:
            firstchild = hdfobj.child()
            if firstchild:
                action = firstchild.name()
                if firstchild.next():
                    raise "multiple actions present!!!"

                method_name = "Action_%s" % action
                method = getattr(self,method_name)
                apply(method,[])

    def start(self):
        SHOULD_DISPLAY = 1
        if self._israwpage:
            SHOULD_DISPLAY = 0
        
        ncgi = self.ncgi
        
        if self.readDefaultHDF:
            try:
                if not self.pagename is None:
                    ncgi.hdf.readFile("%s.hdf" % self.pagename)
            except:
                debug("Error reading HDF file: %s.hdf" % (self.pagename))

        DISPLAY_ERROR = 0
        ERROR_MESSAGE = ""
        # call page main function!
        try:
            self.main()
        except DisplayDone:
            SHOULD_DISPLAY = 0
        except Redirected:
            # catch redirect exceptions
            SHOULD_DISPLAY = 0
        except DisplayError, num:
            ncgi.hdf.setValue("Query.error", str(num))
            if self._error_template:
                ncgi.hdf.setValue("Content", self._error_template)
            else:
                DISPLAY_ERROR = 1
        except:
            SHOULD_DISPLAY = 0
            DISPLAY_ERROR = 1
            
            import handle_error
            handle_error.handleException("Display Failed!")
            ERROR_MESSAGE = handle_error.exceptionString()

        if DISPLAY_ERROR:
            #print "Content-Type: text/html\n\n"

            # print the page

            self['Content-Type'] = "text/html"

            # print the page

            self.push("<H1> Error in Page </H1>\n")
            self.push("A copy of this error report has been submitted to the developers. ")
            self.push("The details of the error report are below.")

            self.push("<PRE>")
            self.push(handle_error.exceptionString())
            self.push("</PRE>\n")

            # print debug info always on page error...
            self.push("<HR>\n")
            self.push("<PRE>")
            self.push(neo_cgi.htmlEscape(ncgi.hdf.dump()))
            self.push("</PRE>")


        etime = time.time() - self.page_start_time
        ncgi.hdf.setValue("CGI.debug.execute_time","%f" % (etime))

        if SHOULD_DISPLAY and self.pagename:
            debug_output = ncgi.hdf.getIntValue("page.debug",ncgi.hdf.getIntValue("Cookie.debug",0))

            # hijack the built-in debug output method...
            if ncgi.hdf.getValue("Query.debug","") == ncgi.hdf.getValue("Config.DebugPassword","1"):
                ncgi.hdf.setValue("Config.DebugPassword","CSPage.py DEBUG hijack (%s)" %
                    ncgi.hdf.getValue("Config.DebugPassword",""))
                debug_output = 1


            if not debug_output:
              ncgi.hdf.setValue("Config.CompressionEnabled","1")

            # default display
            template_name = ncgi.hdf.getValue("Content","%s.cs" % self.pagename)
            # ncgi.hdf.setValue ("cgiout.charset", "utf-8");


            try:
              ncgi.display(template_name)
              self._sent_headers = 1
            except:
              self['Content-Type'] = 'text/html'
              self.push("CSPage: Error occured\n")
              import handle_error
              self.push("<pre>" + handle_error.exceptionString() + "</pre>")
              debug_output = 1
                 
            debug_output = True

            # debug output
            if debug_output:
              self.push("<HR>\n")
              self.push("Execution Time: %5.3f<BR><HR>" % (etime))
              self.push("<PRE>")
              self.push(neo_cgi.htmlEscape(ncgi.hdf.dump()))
              self.push("</PRE>")
              # ncgi.hdf.setValue("hdf.DEBUG",ncgi.hdf.dump())
              # ncgi.display("debug.cs")
                
        script_name = ncgi.hdf.getValue("CGI.ScriptName","")
        if script_name:
            script_name = string.split(script_name,"/")[-1]
            
        log ("[%s] etime/dtime: %5.3f/%5.3f %s (%s)" % (self.domain, etime, time.time() - etime - self.page_start_time,  script_name, self.pagename))
        return self._reply_code

    # a protected output function to catch the output errors that occur when
    # the server is either restarted or the user pushes the stop button on the
    # browser
    def output(self, str):
        try:
          if len(str) > 8196:
            import cStringIO
            fp = cStringIO.StringIO(str)
            while 1:
              data = fp.read(8196*8)
              if not data: break
              self.context.stdout.write(data)
          else:
            self.context.stdout.write(str)
        except IOError, reason:
            log("IOError: %s" % (repr(reason)))
            raise DisplayDone

    def done(self):
      if not self._sent_headers: self.error(500)
      self._sent_headers = 0

      raise DisplayDone

    def push(self, data):
      if not self._sent_headers:
        headerdata = self.send_headers(dont_send=1)
        self.output(headerdata + data)
      else:
        self.output(data)


    def send_headers(self, dont_send=0):
      self._sent_headers = 1

      message = gHTTPResponses[self._reply_code]

      if self._reply_code != 200:
        self['status'] = "%s %s" % (self._reply_code, message)
      self['connection'] = 'close'

      headers = []
      #headers.append(self.response(self._reply_code))
      for (key, value) in self._reply_headers.items():
        headers.append('%s: %s' % (key, value))
      headers.append('\r\n')

      if dont_send == 0:
        self.push(string.join(headers, '\r\n'))
      else:
        return string.join(headers, '\r\n')


    def allQuery (self, s):
        l = []
        if self.ncgi.hdf.getValue ("Query.%s.0" % s, ""):
          obj = self.ncgi.hdf.getChild ("Query.%s" % s)
          while obj:
            l.append(obj.value())
            obj = obj.next()
        else:
          t = self.ncgi.hdf.getValue ("Query.%s" % s, "")
          if t: l.append(t)
        return l


    def error(self, code, reason=None):
      self._reply_code = code
      message = gHTTPResponses[code]
      s = DEFAULT_ERROR_MESSAGE % {
	'code': code, 'message': message, 'reason': reason
      }

#      self['Content-Length'] = len(s)
#      self['Content-Type'] = 'text/html'

#      self.push(s)
      self.context.stdout.write("Content-Type: text/html\n")
      self.context.stdout.write("Status: %s\n" % code)
      self.context.stdout.write(s)
#      self.done()

      raise DisplayDone



gHTTPResponses = {
        100: "Continue",
        101: "Switching Protocols",
        200: "OK",
        201: "Created",
        202: "Accepted",
        203: "Non-Authoritative Information",
        204: "No Content",
        205: "Reset Content",
        206: "Partial Content",
        300: "Multiple Choices",
        301: "Moved Permanently",
        302: "Moved Temporarily",
        303: "See Other",
        304: "Not Modified",
        305: "Use Proxy",
        400: "Bad Request",
        401: "Unauthorized",
        402: "Payment Required",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        406: "Not Acceptable",
        407: "Proxy Authentication Required",
        408: "Request Time-out",
        409: "Conflict",
        410: "Gone",
        411: "Length Required",
        412: "Precondition Failed",
        413: "Request Entity Too Large",
        414: "Request-URI Too Large",
        415: "Unsupported Media Type",
        500: "Internal Server Error",
        501: "Not Implemented",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Time-out",
        505: "HTTP Version not supported"
        }

# Default error message
DEFAULT_ERROR_MESSAGE = string.join(
        ['',
         '<head>',
         '<title>%(code)d %(message)s</title>',
         '</head>',
         '<body>',
         '<h1>%(message)s</h1>',
         '<p>Error code %(code)d.',
         '<p>Message: %(message)s.',
         '<p>Reason:\n <pre>%(reason)s</pre>',
         '</body>',
         ''
         ],
        '\r\n'
        )
