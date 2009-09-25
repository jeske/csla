<HTML>
<HEAD>
  <META http-equiv="Content-Type" content="text/html; charset=utf-8">
  <TITLE> Archive </TITLE>
<STYLE TYPE="text/css">
<!--
  body, td, table { font-family: "trebuchet ms", lucida, verdana, helvetica; 
                    font-size: 14px; }
  .navi0 { font-size: 14px; font-weight: bold; color:white;}
  a.navi0 { color: #ffffff; text-decoration: none}
  a.navi0:visited { color: #cccccc; }
  a.navi0:hover { color: #ee9900; text-decoration: underline; }

  .navi1 { font-size: 14px; font-weight: bold; color:black;}
  a.navi1 { color: #ffffff; text-decoration: none}
  a.navi1:visited { color: #666666; }
  a.navi1:hover { color: #ee9900; text-decoration: underline; }
-->
</STYLE>
</HEAD>

<BODY TOPMARGIN=0 LEFTMARGIN=0 BGCOLOR=white>
<p>
<p>
<table align=center width=80%>
<tr><td>
<b>List of Available Archives:</b><br>
</td></tr>
<?cs each:arc=CGI.Archives ?>
<tr><td>
&nbsp;&middot;&nbsp;<a href="<?cs var:CGI.URIRoot ?><?cs var:arc ?>"><?cs var:arc.Name ?></a>
  <blockquote>
    <?cs var:arc.Description ?>
  </blockquote>
</td></tr>
<?cs /each ?>
</table>


<?cs include:"footer.cs" ?>
