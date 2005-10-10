<?cs include:"header.cs" ?>

<?cs set:month_count = #0 ?>
<?cs each:mon = CGI.Months ?>
  <?cs set:month_count = #month_count + #1 ?>
  <?cs set:last_month = mon ?>
<?cs /each ?>

<p>

<TABLE CELLSPACING=0 CELLPADDING=2>
<TR>
  <TD COLSPAN=2 ALIGN=LEFT><b>Top Authors</b><br></TD>
  <TD COLSPAN=2 ALIGN=LEFT><?cs if:?CGI.MonthPage.NextDate ?><A CLASS=navi1 HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/top_authors?start_date=<?cs var:CGI.MonthPage.NextDate ?>"><font size=-1>&lt;&lt; next</font></A><?cs /if ?></TD>

  <TD COLSPAN="<?cs var:#month_count - #3 ?>" ALIGN=RIGHT><?cs if:?CGI.MonthPage.PrevDate ?><A class=navi1 HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/top_authors?start_date=<?cs var:CGI.MonthPage.PrevDate ?>"><font size=-1>prev &gt;&gt;</font></A></font><?cs /if ?></TD></TR>
  
  </TR>
<TR BGCOLOR=<?cs var:Style.TitleBarColor ?>>
  <TD><font color=white><b>Author</b></font></TD>
  <?cs each:mon = CGI.Months ?>
      <TD nowrap STYLE="border-right=1px solid white;">&nbsp;
        <font color=white><a class=navi0 href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/top_authors?date=<?cs var:mon ?>&start_date=<?cs var:Query.start_date ?>">
	  <?cs if:mon == "total" ?>
	    <b>Total</b>
	  <?cs else ?>
	    <b><?cs var:Lang.Dates.Months_Abbr[mon.month]["val"] ?>-<?cs var:mon.year ?></b>
	  <?cs /if ?>
	 </a>
	</font>&nbsp;
      </TD>
  <?cs /each ?>
</TR>
<?cs set:count = #0 ?>
<?cs each:author = CGI.TopAuthors ?>
  <TR <?cs if:count % #2 == #0 ?>BGCOLOR=<?cs var:Style.CellBGColor ?><?cs /if ?>>
    <TD><A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/author/<?cs var:author.email ?>"><?cs alt:author.name ?><?cs var:author.email ?><?cs /alt ?></A></TD>
    <?cs each:mon = CGI.Months ?>
      <?cs if:mon.hilight ?>
        <TD ALIGN=RIGHT BGCOLOR=<?cs var:Style.ColumnHighlightColor ?>>
      <?cs else ?>
        <TD ALIGN=RIGHT>
      <?cs /if ?>&nbsp;
      <?cs var:author[mon] ?>
      &nbsp;
      </TD>
    <?cs /each ?>
  </TR>
  <?cs set:count = count + #1 ?>
<?cs /each ?>
</TABLE>

<?cs include:"footer.cs" ?>
