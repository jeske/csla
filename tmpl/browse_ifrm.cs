<?cs include:"dates.cs" ?>
<?cs set:Query.noheader = #1 ?>
<?cs include:"header.cs" ?>

<SCRIPT LANGUAGE="JavaScript">
<!--
function month_navigate(f) {
  var date_str = f.options[f.selectedIndex].value;
  document.location.href = "<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/month/" + date_str;
}

//-->
</SCRIPT>

<TABLE WIDTH=100% HEIGHT=100% CELLSPACING=0 CELLPADDING=0>
<TR><TD height=1% colspan=2>
  <?cs evar:CGI.List.Header ?>
  <TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
  <TR><TD BGCOLOR="<?cs var:Style.HeaderBarColor ?>">
  <font face=Arial,Helvetica,sans-serif size=+1><b><A class=navi2 target=_top href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>"><?cs var:CGI.List.EmailAddress ?></A></b></font>
  </TD>
  </TD>
  <TD BGCOLOR="<?cs var:Style.HeaderBarColor ?>" ALIGN=RIGHT>
    <a class=navi1 target=_top href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>">Home</a> | 
    <a class=navi1 target=_top href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/search">Search</a> | 
    <b>Timezone:</b><?cs var:CGI.TimeZone ?> <font size=-1>[<A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/timezone">change</A>]</font>
  </TD></TR></TABLE>
</TD></TR>


<TR>
  <TD width=220 height=1% valign=top>
<TABLE HEIGHT=75 WIDTH=100% CELLSPACING=0 CELLPADDING=2 BGCOLOR=#555555>
<TR><TD COLSPAN=2 BGCOLOR=#444444><B><tt><A TARGET=_top CLASS=navi0 HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>"><?cs var:CGI.List.Name ?></A></tt></TD></TR>
<TR><FORM NAME=monthpulldown><TD>
<CENTER>
<SELECT onchange="month_navigate(this)" STYLE="width:90%" name=month_sel>
  <?cs if:CGI.PathInfo.2 == "month" ?>
    <?cs each:year = CGI.ByMonth ?>
      <?cs each:mon = year ?>
        <?cs if:#mon.count ?>
        <?cs set:mon_num = #mon.mon ?>
        <?cs set:mon_val = mon.year + "-" + mon.mon ?>
        <option value="<?cs var:mon_val ?>" <?cs if:CGI.PathInfo.3 == mon_val ?>SELECTED <?cs /if ?>><?cs var:mon.year ?> - <?cs call:map_val(mon_num, Lang.Dates.Months) ?>
        <?cs /if ?>
      <?cs /each ?>
    <?cs /each ?>
  <?cs /if ?>
</SELECT>
</CENTER>
    </TD></FORM></TR>
</TABLE>
</TD>

<TD WIDTH=100% ROWSPAN=2><iframe frameborder=1 framespacing=0 marginheight=0 marginwidth=0 name=data
width=100% height=100% src="about:blank">You don't support iframes?</iframe></TD>
</TR>

<TR><TD width=220 BGCOLOR=#FFFFFF height=100%>

<div style="overflow: scroll; height:100%; width:220">

<?cs include:"render_index.cs" ?>

</div>
</TD>
</TR>
</TABLE>


<SCRIPT LANGAUGE="JavaScript">
<!--
var TargetFrame = document.data;
setup();
//-->
</SCRIPT>
