<?cs include:"dates.cs" ?>
<?cs include:"header.cs" ?>

<p>

<?cs def:thread_nav(a) ?>
<TABLE CELLSPACING=0 CELLPADDING=2 WIDTH=100%>
<TR><TD>Threads <?cs var:CGI.ThreadsPage.CurStart ?> - <?cs var:CGI.ThreadsPage.CurEnd ?> of <?cs var:CGI.ThreadsPage.MaxThreadNum ?></TD>
    <TD ALIGN=RIGHT>
      <?cs if:?CGI.ThreadsPage.PrevStart ?>
        <A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/threads?start=<?cs var:CGI.ThreadsPage.PrevStart ?>">&lt;&lt; Prev <?cs var:CGI.ThreadsPage.Count ?> threads</A>&nbsp;&nbsp;
      <?cs /if ?>
      <?cs if:?CGI.ThreadsPage.NextStart ?>
        <A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/threads?start=<?cs var:CGI.ThreadsPage.NextStart ?>">Next <?cs var:CGI.ThreadsPage.Count ?> threads &gt;&gt;</A>
      <?cs /if ?>
    </TD></TR>
</TABLE>

<?cs /def ?>

<?cs call:thread_nav("foo") ?>

<TABLE CELLSPACING=0 CELLPADDING=2 WIDTH=100%>
<TR BGCOLOR=#CCCCCC>
    <TD WIDTH=1%><b>Date</b></TD>
    <TD><b>Thread Subject</b></TD>
    <TD WIDTH=25%><b>Most Recent Poster</b></TD>
</TR>
<?cs set:alt_row = #0 ?>
<?cs each:msg = CGI.Threads ?>
<TR BGCOLOR="<?cs if:#alt_row ?><?cs var:Style.AltRowColor ?><?cs else ?><?cs var:Style.RowColor ?><?cs /if ?>"><TD VALIGN=TOP NOWRAP><?cs call:Date.abbr_short(msg.date) ?></TD>
    <TD VALIGN=TOP><A HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/thread/<?cs var:msg.thread_id ?>/<?cs var:msg.doc_id ?>"><?cs var:msg.subject_strip ?></A> (<?cs if:msg.count > #1 ?><?cs var:msg.count ?> articles<?cs else ?>1 article<?cs /if ?>)</TD>
    <TD VALIGN=TOP><?cs alt:msg.author ?><?cs var:msg.email ?><?cs /alt ?></TD></TR>

  <?cs if:#alt_row ?> 
    <?cs set:alt_row = #0 ?>
  <?cs else ?>
    <?cs set:alt_row = #1 ?>
  <?cs /if ?>

<?cs /each ?>
<TR BGCOLOR=#CCCCCC>
    <TD><b>Date</b></TD>
    <TD><b>Thread Subject</b></TD>
    <TD><b>Most Recent Poster</b></TD>
</TR>
</TABLE>

<?cs call:thread_nav("foo") ?>

<?cs include:"footer.cs" ?>
