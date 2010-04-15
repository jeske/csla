


Archive - A clearsilver-templating based mailing list archive interface.




INSTALLING
----------


1. Install Python 2.6
2. Install clearsilver from clearsilver.net, and be sure the python 
   module is installed in the active python interpreter

IF you want text-search support, then...

3. Install Swish-e full-text indexing from swish-e.org
4. Install the Swish-E python module from http://pypi.python.org/pypi/Swish-E/0.5

IMPORT A LIST
-------------

 discuss/pysrc/index.py --listname <listname> <your mbox files ... >


SETUP WEB INTERFACE
-------------------

Install the web-CGI into Apache or your local webserver. The Apache directives I use to add it to my configuration are:

  Alias /discuss2/tmpl/ "/home/jeske/src/archive/discuss/tmpl/"
  ScriptAlias /discuss2/ "/home/jeske/src/archive/discuss/pysrc/bin/discuss.py/"

  <Directory "/home/jeske/src/archive/discuss/pysrc/bin/">
  SetEnv DISCUSS_DATA_ROOT "/home/jeske/src/archive/blender"
  AllowOverride All
  Options +ExecCGI
  Order allow,deny
  Allow from All
  </Directory>


HOOKUP LIVE MAIL IMPORTING
--------------------------





TROUBLESHOOTING
---------------

If your apache does not have the right path to launch the right version of
python or your swish-e tool, you can usually fix it by editing your local
httpd/bin/envvars file.  




