"""
  Copyright (C) 2000-2001  Brandon Long <blong@fiction.net>

  VirtualBrowser - a controllable/scriptable web agent
"""

VERSION = "0.10"

import sys, string, re
import timeoutsocket
timeoutsocket.setDefaultSocketTimeout(20)

import urllib
import httplib
import Cookie

class VirtualBrowser:
  def __init__ (self, auth_callback = None, dl_callback = None, ul_callback = None):
    self._user_agent = "VirtualBrowser/%s" % VERSION

    self._current_url = None
    self._host = "localhost"
    self._last_url = None
    self._cookies = {}
    self._auth_cache = {}

    self._extra_headers = []
    self._languages = ["en"]
    self._types = ["text/html", "text/plain", "image/jpeg", "image/gif"]

    # We open URLs we don't understand with urllib
    self._fallback_opener = urllib.URLopener()

    # HTTP traffic timesout in 120 seconds
    self._timeout = 15

    # Callback function provided by user to get user/pass auth
    self._auth_callback = auth_callback
    self._dl_callback = dl_callback
    self._ul_callback = ul_callback

  def timeout_ (self, o):
    try:
      self._timeout = int (o)
    except ValueError:
      pass
    return self

  def headers_(self, o):
    self._extra_headers = o
    return self

  def fetchpage (self, url, realm=None, oheaders=[]):
    if self._last_url:
      url = urllib.basejoin (self._last_url, url)
    self._current_url = url
    type, rest = urllib.splittype (url)
    if not type:
      type = "http"
    host, path = urllib.splithost (rest)
    if not host:
      host = self._host
    else:
      self._host = host
    host, port = urllib.splitport (host)

    if type == "http":
      errcode, errmsg, page, headers = self.fetch_http (host, port, path, realm=realm, oheaders=oheaders)
      self._last_url = self._current_url
      return errcode, errmsg, page, headers
    else:
      return self._fallback_opener.retrieve (url)
      
  def fetch_http (self, host, port, path, realm = None, method = "GET", body = None, ctype = None, oheaders=[]):
    if not port:
      port = 80
    else:
      try:
        port = int (port)
      except ValueError:
        port = 80

    cookie = self.getCookie (host, path)

    timeoutsocket.setDefaultSocketTimeout(20)
    
    h = httplib.HTTP (host, port)
    if method:
      h.putrequest (method, path)
    else:
      h.putrequest ("GET", path)
    h.putheader ("Host", host)
    h.putheader ("User-Agent", self._user_agent)
    h.putheader ("Accept", string.join (self._types, ", "))
    h.putheader ("Accept-Language", string.join (self._languages, ", "))
    if self._last_url:
      h.putheader ("Referer", self._last_url)
    if cookie:
      h.putheader ("Cookie", cookie)
    if realm:
      auth = self.getAuth (host, port, realm)
      h.putheader ("Authorization", "Basic %s" % auth)
    if ctype:
      h.putheader ("Content-Type", ctype)
    if body:
      h.putheader ("Content-Length", str(len(body)))
    for (k, v) in oheaders:
      h.putheader (k, v)
    for (k, v) in self._extra_headers:
      h.putheader (k, v)
      
    h.endheaders ()

    if self._ul_callback is not None:
        while 1:    
            buf = self._ul_callback()
            if buf is None: break
            h.send(buf)
    elif body:
      h.send(body)

    errcode, errmsg, headers = h.getreply()

    f = h.getfile()
    if self._dl_callback is not None:
        self._dl_callback(f)
        page = ""
    else:
        page = f.read()
    f.close()

    if errcode == -1:
      return errcode, errmsg, page, headers

    if headers.has_key ("set-cookie"):
      # This isn't actually "headers" its a MimeMessage (rfc822.Message)
      # And, when you have more than one instance of a header, you have
      # to (sigh) ask for all matching, then decode them yourself
      for line in headers.getallmatchingheaders ("set-cookie"):
        header, value = string.split (line, ':', 1)
        m = Cookie.Morsel (string.strip(value))
        self.addCookie (m, host)

    if errcode == 302:
      self._last_url = self._current_url
      newurl = headers['location']
      return self.fetchpage(newurl)

    if errcode == 401:
      if headers.has_key('www-authenticate'):
        auth_header = headers['www-authenticate']
        match = re.match('[ \t]*([^ \t]+)[ \t]+realm="([^"]*)"', auth_header)
        if match:
          scheme, realm = match.groups()
          headers['virtualbrowser-auth-scheme'] = scheme
          headers['virtualbrowser-auth-realm'] = realm
          if string.lower(scheme) == 'basic':
            # Only attempt retry if we have an authorization to attempt
            if self.getAuth (host, port, realm):
              return self.fetch_http (host, port, path, realm)
            

    return errcode, errmsg, page, headers

  def do_post (self, url, post_dict, ctype="application/x-www-form-urlencoded", oheaders=[]):
    if self._last_url:
      url = urllib.basejoin (self._last_url, url)
    self._current_url = url
    type, rest = urllib.splittype (url)
    if not type:
      type = "http"
    host, path = urllib.splithost (rest)
    if not host:
      host = self._host
    else:
      self._host = host
    host, port = urllib.splitport (host)

    data = urllib.urlencode(post_dict)
    errcode, errmsg, page, headers = self.fetch_http (host, port, path, method = "POST", body = data, ctype = ctype)
    self._last_url = self._current_url
    return errcode, errmsg, page, headers

  def do_put (self, url, data, ctype="application/octet-stream", oheaders=[]):
    if self._last_url:
      url = urllib.basejoin (self._last_url, url)
    self._current_url = url
    type, rest = urllib.splittype (url)
    if not type:
      type = "http"
    host, path = urllib.splithost (rest)
    if not host:
      host = self._host
    else:
      self._host = host
    host, port = urllib.splitport (host)

    errcode, errmsg, page, headers = self.fetch_http (host, port, path, method = "PUT", body = data, ctype = ctype, oheaders=oheaders)
    self._last_url = self._current_url
    return errcode, errmsg, page, headers

  def getAuth (self, host, port, realm):
    key = '%s@%s:%s' % (realm, string.lower (host), port)
    if self._auth_cache.has_key(key):
      return self._auth_cache[key]
    if self._auth_callback:
      user, password = self._auth_callback
      return self.addAuth ('%s:%s' % (host, port), realm, user, password)
    return None

  def addAuth (self, host, realm, user, password):
    import base64
    key = realm + '@' + string.lower (host)
    up = "%s:%s" % (user, password)
    auth = string.strip (base64.encodestring(up))
    self._auth_cache[key] = auth
    return auth

  def getCookie (self, host, path):
    cookie_str = []
    hlen = len (host)
    for domain, cpath in self._cookies.keys():
      dlen = len (domain) 
      if (host[hlen-dlen:] == domain) and (path[:len(cpath)] == cpath):
        for morsel in self._cookies[(domain, cpath)]:
          cookie_str.append ("%s=%s" % (morsel.key, morsel.value))

    if cookie_str == []:
      return None
    return string.join (cookie_str, '; ')

  def addCookie (self, morsel, host):
    try:
      domain = morsel['domain']
    except KeyError:
      domain = host
    try:
      path = morsel['path']
    except KeyError:
      path = '/'

    uniq = (domain, path)
    if self._cookies.has_key (uniq):
      for sm in self._cookies[uniq]:
        if sm.key == morsel.key:
          self._cookies[uniq].remove(sm)
      self._cookies[uniq].append (morsel)
    else:
      self._cookies[uniq] = [morsel]


