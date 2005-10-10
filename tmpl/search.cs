<?cs include:"dates.cs" ?>
<?cs include:"header.cs" ?>

<table align=center>
      <form name="searchform" action="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/search" method="get">
        <tr valign=middle>
          <td nowrap>
	    <input type="text" name="query" size="25" value="<?cs var:html_escape(Query.query) ?>">&nbsp;  
	    <input type="submit" name=submit value="Search Archive">
          </td>
        </tr>
      </form>
</table>

<?cs if:?Query.query ?>
<TABLE WIDTH=100% CELLSPACING=0 CELLPADDING=2>
<TR BGCOLOR=#EEEEEE><TD>
Searched for '<b><?cs var:html_escape(Query.query) ?></b>'
</TD><TD ALIGN=RIGHT>
<?cs if:!CGI.SearchNoResults ?>
Results <b><?cs var:CGI.SearchStart ?>-<?cs var:CGI.SearchEnd ?></b> of <b><?cs var:CGI.SearchTotal ?></b>. Search took <b><?cs var:CGI.SearchTime ?></b> seconds.
<?cs /if ?>
</TD></TR>
<?cs if:!CGI.SearchNoResults ?>
<TR BGCOLOR=#EEEEEE><TD COLSPAN=2 ALIGN=RIGHT>
<a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/search?query=<?cs var:url_escape(Query.query) ?>">Browse results</a>
</TD></TR>
<?cs /if ?>
</TABLE>

<p>

<?cs if:CGI.SearchNoResults ?>
  <div align=center>
    <font color=red>
      No results matched the query <b><?cs var:html_escape(Query.query) ?></b>
    </font>
  </div>
<?cs else ?>

<DIV STYLE="margin:0px 0px 0px 50px;padding-left:0px;">
<?cs each:match = CGI.Matches ?>
<font face="helvetica" size=-1>
<P>
<a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/msg/<?cs var:match.doc_id ?>"><?cs var:match.subject ?></a><br>
<?cs var:match.Snippet ?><br>
<font color=green>
<?cs if:match.author ?>
  "<?cs var:match.author ?>" &lt;<?cs var:match.email ?>&gt;
<?cs else ?>
  <?cs var:match.email ?>
<?cs /if ?>
</font>
- <?cs call:Date.num_date(match.date) ?> 
<a style="color:green;" href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/thread/<?cs var:match.thread_id ?>/<?cs var:match.doc_id ?>">View Thread (<?cs if:match.thread_count > #1 ?><?cs var:match.thread_count ?> articles<?cs else ?>1 article<?cs /if ?>)</a>
<?cs /each ?>
</DIV>


<div align=center>
  Page: <?cs if:CGI.SearchPage != #1 ?><a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/search?query=<?cs var:url_escape(Query.query) ?>&page=<?cs var:CGI.SearchPage - #1 ?>">Previous</a>&nbsp;<?cs /if?>
  <?cs loop:page=#CGI.SearchPageStart,#CGI.SearchPageEnd ?>
    <?cs if:page == CGI.SearchPage ?>
      <?cs var:page ?>&nbsp;
    <?cs else ?>
      <a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/search?query=<?cs var:url_escape(Query.query) ?>&page=<?cs var:page ?>"><?cs var:page ?></a>&nbsp;
    <?cs /if ?>
  <?cs /loop ?>
  <?cs if:CGI.SearchPage != CGI.SearchPages ?><a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/search?query=<?cs var:url_escape(Query.query) ?>&page=<?cs var:CGI.SearchPage + #1 ?>">Next</a><?cs /if?>
</div>
<?cs /if ?>

<?cs /if ?>

<?cs include:"footer.cs" ?>
