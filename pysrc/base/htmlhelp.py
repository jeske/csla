#!/neo/opt/bin/python

# htmlhelp.py

import string
import re
import neo_cgi


# --- For these ---
# & -> &amp;
# < -> &lt;
# > -> &gt;
# ? -> %3f
#
# use neo_cgi.htmlEscape(string)

replace_dict = {}
for a_char in ['&','<','>','?', ' ', '=']:
    replace_dict[a_char] = "%%%X" % ord(a_char)

def urlEscape(str):
    global replace_dict
    
    new_str = ""
    for a_char in str:
	if replace_dict.has_key(a_char):
	    new_str = new_str + replace_dict[a_char]
	else:
	    new_str = new_str + a_char

    return new_str

NON_BREAKING_HYPHEN = "&#8209;"

def emailEscape(addr):
    return neo_cgi.htmlEscape(addr)

    # this was causing problems with delivery to these email addresses
    #  - jeske
    # return string.replace(neo_cgi.htmlEscape(addr),"-",NON_BREAKING_HYPHEN)


#################
# jsEscape(str)
#
# escape a string for use inside a javascript string

js_replace = {}
for a_char in ["'",'"',"\n","\r","\t","\\",">",">","&"]:
    js_replace[a_char] = "\\x%02X" % ord(a_char)

def jsEscape(str):
    global js_replace
    
    
    new_str = ""
    for a_char in str:
        if js_replace.has_key(a_char):
            new_str = new_str + js_replace[a_char]
        else:
            new_str = new_str + a_char

    return new_str


def name_case(a_str):
    if len(a_str):
      a_str = string.upper(a_str[0]) + string.lower(a_str[1:])

    return a_str
def split_name(a_name):
    if not a_name:
        return ""

    last_name = ""

    comma_sep_parts = string.split(string.strip(a_name),",")
    if len(comma_sep_parts) > 1:
        try:
            first_name = string.split(comma_sep_parts[1])[0]
        except IndexError:
            first_name = comma_sep_parts[1]
        last_name  = string.strip(comma_sep_parts[0])
    else:
        parts = string.split(string.strip(a_name)," ")
        first_name = parts[0]
        if len(parts) > 1:
            last_name = parts[-1]

    return name_case(first_name),name_case(last_name)

    




