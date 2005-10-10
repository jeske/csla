<?xml version="1.0" ?>
<?cs include:"dates.cs" ?>
<?cs set:base_url = "http://" + CGI.ServerName ?>
<?cs if:CGI.ServerPort != #80 ?>
  <?cs set:base_url = base_url + ":" + CGI.ServerPort ?>
<?cs /if ?>
<?cs set:archive_url = base_url + CGI.URIRoot + CGI.ArchiveName ?>
<rss version="0.92">
<channel>
  <title>Archive: <?cs var:CGI.List.Title ?></title>
  <link><?cs var:archive_url ?></link>
  <description><?cs var:html_escape(CGI.List.Description) ?></description>
  <language><?cs alt:CGI.List.Language ?>en<?cs /alt ?></language>
  <?cs each:msg=CGI.Messages ?>
    <item>
      <title><?cs var:html_escape(msg.Subject) ?></title>
      <link><?cs var:archive_url ?>/msg/<?cs var:msg.doc_id ?></link>
      <description>
        <?cs var:html_escape(html_strip(msg.summary)) ?>
      </description>
    </item>
  <?cs /each ?>
</channel>
</rss>
