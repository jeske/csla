<?cs include:"header.cs" ?>
<?cs include:"dates.cs" ?>

<TABLE WIDTH=100%><TR>
<TD WIDTH=40% VALIGN=TOP>

<TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
<TR><TD BGCOLOR=<?cs var:Style.TitleBarColor ?> CLASS=navi0>Description</TD></TR>
</TABLE>
<?cs var:CGI.List.Description ?>

<p>

<TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
<TR><TD BGCOLOR=<?cs var:Style.TitleBarColor ?> CLASS=navi0>New Activity</TD></TR>
</TABLE><TABLE BGCOLOR=#FFFFFF WIDTH=100% CELLSPACING=0 CELLPADDING=2>

<?cs if:?CGI.LastVisit.Date.year ?>
  <TR><TD COLSPAN=2><br>Since your last visit on <b><?cs var:CGI.LastVisit.Date.year ?>/<?cs var:CGI.LastVisit.Date.mon ?>/<?cs var:CGI.LastVisit.Date.mday ?></b>:</TD></TR>

  <TR WIDTH=30% BGCOLOR=<?cs var:Style.CellBGColor ?>><TD ALIGN=RIGHT><?cs var:CGI.LastVisit.NewMessages ?></TD><TD>New Messages</TD></TR>
  <TR BGCOLOR=<?cs var:Style.CellBGColor ?>><TD ALIGN=RIGHT><?cs var:CGI.LastVisit.NewThreads ?></TD><TD><A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/threads?start=1">New Threads</A></TD></TR>
<?cs /if ?>

  <TR BGCOLOR=<?cs var:Style.CellBGColor ?>><TD ALIGN=center colspan=2>Browse Latest as: <br><A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/threads?start=1">Thread List</A> | 
	       <a target=_top href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/month/">Tree</a>
</TD></TR>

<?cs if:?CGI.NewPosts.0.Range ?>
 <TR><TD COLSPAN=2><br>New Posts:</TD></TR>
<?cs each:newposts=CGI.NewPosts ?>
 <TR BGCOLOR=<?cs var:Style.CellBGColor ?>><TD ALIGN=RIGHT><?cs var:newposts.Range ?></TD><TD>...since <?cs var:newposts.Date.year ?>/<?cs var:newposts.Date.mon ?>/<?cs var:newposts.Date.mday ?></TD></TR>
<?cs /each ?>
<?cs /if ?>

<?cs if:#0 ?>
 <TR><TD COLSPAN=2><br>Watched Authors:</TD></TR>
 <TR BGCOLOR=<?cs var:Style.CellBGColor ?>><TD ALIGN=RIGHT>25</TD><TD><A HREF="c_new_threads.cs">Miguel de Icaza</A></TD></TR>
 <TR BGCOLOR=<?cs var:Style.CellBGColor ?>><TD ALIGN=RIGHT>5</TD><TD><A HREF="c_new_threads.cs">Daniel Stodden</A></TD></TR>
<?cs /if ?>

</TABLE>
<p>
<TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
<TR><TD BGCOLOR=<?cs var:Style.TitleBarColor ?> CLASS=navi0>Feeds</TD></TR>
</TABLE>
<TABLE>
<TR><td><b>Recent Messages</b>: 
<a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/rss92/new.xml">RSS 0.92</a> -
<a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/rss10/new.xml">RSS 1.0</a> -
<a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/rss20/new.xml">RSS 2.0</a> 
<br>
<TR>
    <TD ALIGN=RIGHT><i><A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/feeds">more...</A></i></TD></TR>
</TABLE>

<p>
<TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
<TR><TD BGCOLOR=<?cs var:Style.TitleBarColor ?> CLASS=navi0>Did you know?</TD></TR>
</TABLE>
That you can choose between <b>no frames</b>, <b>frames</b>, and <b>iframes</b> modes, 
or even share read/unread status with multiple machines? For this and more, check
out the <A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/prefs">Preferences</a>
page.




</TD><TD VALIGN=TOP>

<TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
<TR><TD BGCOLOR=<?cs var:Style.TitleBarColor ?> CLASS=navi0>Most Recent Posts</TD></TR>
</TABLE>
<TABLE WIDTH=100%>
<?cs each:msg = CGI.RecentMessages ?>
  <TR><TD VALIGN=TOP NOWRAP><?cs call:Date.abbr_short(msg.date) ?></TD>
      <TD><A <?cs if:#msg.doc_id.IsRead ?>class=vlnk<?cs /if ?> HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/msg/<?cs var:msg.doc_id ?>"><?cs var:msg.subject ?></A><br>
          <tt><?cs var:msg.summary ?></tt> (<?cs alt:msg.author ?><?cs var:msg.email ?><?cs /alt ?>)
      </TD></TR>
<?cs /each ?>

</TABLE>



<TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
<TR><TD BGCOLOR=<?cs var:Style.TitleBarColor ?> CLASS=navi0>Archive</TD></TR>
</TABLE>

<table align=center>
      <form name="searchform" action="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/search" method="get">
        <tr valign=middle>
          <td nowrap>
	    <input type="text" name="query" size="25">&nbsp;  
	    <input type="submit" name=submit value="Search Archive">
          </td>
        </tr>
      </form>
</table>


<table width="90%" vspace=0 hspace=0 cellpadding=3 cellspacing=1 border=0 align=center>
  <tr>
    <td><font size="-1"></font></td>
      <td nowrap><font size="-1">&nbsp;Jan</font></td>
      <td nowrap><font size="-1">&nbsp;Feb</font></td>
      <td nowrap><font size="-1">&nbsp;Mar</font></td>
      <td nowrap><font size="-1">&nbsp;Apr</font></td>
      <td nowrap><font size="-1">&nbsp;May</font></td>
      <td nowrap><font size="-1">&nbsp;Jun</font></td>
      <td nowrap><font size="-1">&nbsp;Jul</font></td>
      <td nowrap><font size="-1">&nbsp;Aug</font></td>
      <td nowrap><font size="-1">&nbsp;Sep</font></td>
      <td nowrap><font size="-1">&nbsp;Oct</font></td>
      <td nowrap><font size="-1">&nbsp;Nov</font></td>
      <td nowrap><font size="-1">&nbsp;Dec</font></td>
  </tr>
    <?cs each:year = CGI.ByMonth ?>
      <tr>
	<td nowrap><font size="-1"><?cs name:year ?></font></td>
	<?cs each:mon = year ?>
	    <td nowrap bgcolor="<?cs var:Style.CellBGColor ?>" align=center><font size="-1">&nbsp;
	      <?cs if:#mon.count ?>
	       <a target=_top href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/month/<?cs var:mon.year ?>-<?cs var:mon.mon ?>/<?cs var:mon.count ?>"><?cs var:mon.count ?></a></font>
	       <?cs /if ?>
	    </td>
	<?cs /each ?>
      </tr>
    <?cs /each ?>
</table>


<TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
<TR><TD BGCOLOR=<?cs var:Style.TitleBarColor ?> CLASS=navi0>Top Authors</TD></TR>
</TABLE>

<TABLE WIDTH=100%>
<TR><TD BGCOLOR=<?cs var:Style.SubHeaderBarColor ?> width=48%>This Month</TD>
    <TD>&nbsp;</TD>
    <TD BGCOLOR=<?cs var:Style.SubHeaderBarColor ?> width=48%>Total</TD></TR>
<TR>
  <TD valign=top>
    <TABLE WIDTH=100%>
      <?cs if:#CGI.TopAuthors.Now ?>
      <?cs each:top_author = CGI.TopAuthors.Now ?>
	<TR>
	  <TD ALIGN=RIGHT WIDTH=12%><?cs var:top_author.count ?></TD><TD><A TARGET=_top HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/author/<?cs var:url_escape(top_author.email) ?>/month/<?cs var:CGI.TopAuthors.NowDate ?>"><?cs alt:top_author.name ?><?cs var:top_author.email ?><?cs /alt ?></A></TD>
	</TR>
      <?cs /each ?>
      <TR><TD COLSPAN=2 ALIGN=RIGHT><i><A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/top_authors?date=<?cs var:CGI.TopAuthors.NowDate ?>">more...</TD></TR>
      <?cs else ?>
        <tr><td align=center><i>None</i></td></tr>
      <?cs /if ?>
    </TABLE>
  </TD>
  <TD>&nbsp;</TD>
  <TD>
    <TABLE WIDTH=100%>
      <?cs each:top_author = CGI.TopAuthors.Total ?>
	<TR>
	  <TD ALIGN=RIGHT WIDTH=12%><?cs var:top_author.count ?></TD><TD><A TARGET=_top HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/author/<?cs var:url_escape(top_author.email) ?>"><?cs alt:top_author.name ?><?cs var:top_author.email ?><?cs /alt ?></A></TD>
	</TR>
      <?cs /each ?>
      <TR><TD COLSPAN=2 ALIGN=RIGHT><i><A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/top_authors?date=total">more...</TD></TR>
    </TABLE>
  </TD>
</TR>
</TABLE>


</TD></TR>
</TABLE>

<?cs include:"footer.cs" ?>
