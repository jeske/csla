<?cs include:"dates.cs" ?>
<?cs include:"header.cs" ?>

<?cs def:render_range_header(top) ?>
<table border=0 cellspacing=0>
<tr><td bgcolor=#26A491><font color=#ffffff>&nbsp;<?cs var:CGI.First ?> - <?cs var:CGI.Last ?> of <?cs var:CGI.Total ?>
&nbsp;&nbsp;&nbsp;
<?cs if:CGI.Prev ?>
<a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/index/<?cs var:CGI.Prev ?>">Prev</a>
<?cs else ?>
Prev
<?cs /if ?> | <?cs if:CGI.Next ?>
<a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/index/<?cs var:CGI.Next ?>">Next</a>
<?cs else ?>
Next
<?cs /if ?>
&nbsp;&nbsp;&nbsp;
<a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/index/0 ?>">First</a>
 | 
<a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/index/">Last</a>
</font></td></tr>
</table>
<?cs /def ?>

<?cs call:render_range_header(#1) ?>
<?cs set:count = #0 ?>
<table border=0 style="font-size:10pt" cellspacing=0>
<?cs each:idx = CGI.Index ?>
  <?cs set:count = #count + #1 ?>
  <?cs if:#count % #2 ?>
    <?cs set:bgcolor = "#eeeeee" ?>
  <?cs else ?>
    <?cs set:bgcolor = "#cccccc" ?>
  <?cs /if ?>
  <tr bgcolor=<?cs var:bgcolor ?>>
    <td><a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/thread/<?cs var:idx.thread_id ?>">[t]</a></td>
    <td><a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/msg/<?cs var:idx.doc_id ?>"><?cs var:idx.subject ?></a></td>
    <td><a href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/search?query=%22<?cs var:idx.email ?>%22"><?cs var:idx.author ?></td>
    <td nowrap><?cs call:Date.num_date(idx.date) ?></td>
  </tr>
<?cs /each ?>
</table>
<?cs call:render_range_header(#0) ?>

</BODY>
</HTML>
