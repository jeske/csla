<?cs include:"dates.cs" ?>
<HTML>
<HEAD>
<STYLE TYPE="text/css">
<!--
  body, td, table { font-family: "trebuchet ms", lucida, verdana, helvetica; 
                    font-size: 14px; color:white; }
  .navi0 { font-size: 14px; }
  a.navi0 { color: #ffffff; text-decoration: none}
  a.navi0:visited { color: #cccccc; }
  a.navi0:hover { color: #ee9900; text-decoration: underline; }
-->
</STYLE>
<script language="JavaScript1.2">
<!--

<?cs include:"js_common.cs" ?>

var avail_dates = new Array();
var avail_dates_names = new Array();
<?cs each:year = CGI.ByMonth ?>
  <?cs each:mon = year ?>
    <?cs if:#mon.count ?>
    avail_dates['<?cs var:mon.year ?>-<?cs var:mon.mon ?>'] = '<?cs var:mon.year ?>-<?cs var:mon.mon ?>'
    <?cs set:mon_num = #mon.mon ?>
    avail_dates_names['<?cs var:mon.year ?>-<?cs var:mon.mon ?>'] = '<?cs var:mon.year ?> - <?cs call:map_val(mon_num, Lang.Dates.Months) ?>'
    <?cs /if ?>
  <?cs /each ?>
<?cs /each ?>

function month_navigate(f) {
  var date_str = f.month_sel.options[f.month_sel.selectedIndex].value;
  parent.location.href = "<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/month/" + date_str;
}

//-->
</script>
</HEAD>
<BODY BGCOLOR=<?cs var:Style.TitleBarColor ?>>

<TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
<TR><TD COLSPAN=2><B><tt><A TARGET=_top CLASS=navi0 HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>"><?cs var:CGI.List.Name ?></A></tt></TD></TR>
<TR>
    <TD ALIGN=CENTER WIDTH=100% NOWRAP>
      <?cs if:#0 ?>
        <b>Thread</b> | <A CLASS=navi0 HREF="#">Date</A> | <A CLASS=navi0 HREF="#">Author</A>
      <?cs /if ?>
    </TD></TR>
<form name=f_nav target=_top action="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/<?cs var:CGI.PathInfo.2 ?>">
<TR><TD>
<CENTER>
<?cs if:CGI.PathInfo.2 == "month" ?>
<SELECT onchange="month_navigate(this.form)" STYLE="width:90%" name=month_sel>
    <?cs each:year = CGI.ByMonth ?>
      <?cs each:mon = year ?>
        <?cs if:#mon.count ?>
        <?cs set:mon_num = #mon.mon ?>
        <?cs set:mon_val = mon.year + "-" + mon.mon ?>
        <option value="<?cs var:mon_val ?>" <?cs if:CGI.PathInfo.3 == mon_val ?>SELECTED <?cs /if ?>><?cs var:mon.year ?> - <?cs call:map_val(mon_num, Lang.Dates.Months) ?>
        <?cs /if ?>
      <?cs /each ?>
    <?cs /each ?>
</SELECT>
<?cs elif:CGI.PathInfo.2 == "search" ?>
Query: <input type=text name=query value="<?cs var:html_escape(Query.query) ?>">
<?cs /if ?>
</CENTER>
    </TD></TR>
</form>
</TABLE>

</BODY>
</HTML>
