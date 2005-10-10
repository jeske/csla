<HTML>
<HEAD>
  <META http-equiv="Content-Type" content="text/html; charset=utf-8">
  <TITLE> Archive: <?cs var:CGI.ArchiveName ?> </TITLE>
<STYLE TYPE="text/css">
<!--
  td { font-family:"Arial,Helvetica,sans-serif";}
  td.hdr { background:<?cs var:Style.Msg.HeaderBGColor ?>; color:white; }
  body.hdr, td.navi0, table.hdr { font-family: "trebuchet ms", lucida, verdana, helvetica; 
                    font-size: 14px; }
  .navi0 { font-size: 14px; font-weight: bold; color:white;}
  a.navi0 { color: #ffffff; text-decoration: none}
  a.navi0:visited { color: #cccccc; }
  a.navi0:hover { color: #ee9900; text-decoration: underline; }

  .navi1 { font-weight: bold; color:black;}
  a.navi1 { color: black; text-decoration: none}
  a.navi1:hover { color: #995500; text-decoration: underline; }

  a.navi2 { color: black; text-decoration: none}
  a.navi2:hover { color: #995500; text-decoration: underline; }

A:link { color:<?cs var:Style.A_link ?>; }
A:visited { color:<?cs var:Style.A_visited ?>; }
A:active { color:<?cs var:Style.A_active ?>; }
A:hover { color:<?cs var:Style.A_hover ?>; }

A.lnk:link { color:<?cs var:Style.A_link ?>; }
A.lnk:visited { color:<?cs var:Style.A_visited ?>; }
A.lnk:active { color:<?cs var:Style.A_active ?>; }
A.lnk:hover { color:<?cs var:Style.A_hover ?>; }

A.vlnk { color:<?cs var:Style.A_visited ?>; }
A.vlnk:link { color:<?cs var:Style.A_visited ?>; }
A.vlnk:visited { color:<?cs var:Style.A_visited ?>; }
A.vlnk:active { color:<?cs var:Style.A_active ?>; }
A.vlnk:hover { color:<?cs var:Style.A_hover ?>; }

// -->
</STYLE>
</HEAD>

<?cs def:msgclass(msg) ?>
  <?cs if:#msg.doc_id.IsRead ?>class=vlnk<?cs /if ?>
<?cs /def ?>

<BODY TOPMARGIN=0 LEFTMARGIN=0 MARGINWIDTH=0 MARGINHEIGHT=0 BGCOLOR=white>


<?cs if:!?Query.noheader ?>
  <?cs evar:CGI.List.Header ?>
  <TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
  <TR><TD BGCOLOR="<?cs var:Style.HeaderBarColor ?>">
  <font face=Arial,Helvetica,sans-serif size=+1><b><A class=navi2 target=_top href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>"><?cs var:CGI.List.EmailAddress ?></A></b></font>
  </TD>
  </TD>
  <TD BGCOLOR="<?cs var:Style.HeaderBarColor ?>" ALIGN=RIGHT>
    <a class=navi1 target=_top href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>">Home</a> | 
    <a class=navi1 target=_top href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/search">Search</a> | 
    <a class=navi1 target=_top href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/prefs">Prefs</a> | 
    <b>Timezone:</b><?cs var:CGI.TimeZone ?> <font size=-1>[<A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/prefs">change</A>]</font>
  </TD></TR></TABLE>
<?cs /if ?>
