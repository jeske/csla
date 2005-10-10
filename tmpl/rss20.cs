<?xml version="1.0" ?>
<?cs include:"dates.cs" ?>
<?cs set:base_url = "http://" + CGI.ServerName ?>
<?cs if:CGI.ServerPort != #80 ?>
  <?cs set:base_url = base_url + ":" + CGI.ServerPort ?>
<?cs /if ?>
<?cs set:archive_url = base_url + CGI.URIRoot + CGI.ArchiveName ?>
<rss version="2.0"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns="http://purl.org/rss/1.0/"
>
<channel>
  <title>Archive: <?cs var:CGI.List.Title ?></title>
  <link><?cs var:archive_url ?></link>
  <description><?cs var:html_escape(CGI.List.Description) ?></description>
  <dc:publisher><?cs var:CGI.List.EmailAddress ?></dc:publisher>
  <dc:language><?cs alt:CGI.List.Language ?>en<?cs /alt ?></dc:language>
  <?cs each:msg=CGI.Messages ?>
    <item>
      <title><?cs var:html_escape(msg.Subject) ?></title>
      <link><?cs var:archive_url ?>/msg/<?cs var:msg.doc_id ?></link>
      <description>
        <?cs var:html_escape(html_strip(msg.summary)) ?>
      </description>
      <guid isPermaLink="true"><?cs var:archive_url ?>/msg/<?cs var:msg.doc_id ?></guid>
      <dc:creator><?cs alt:msg.author ?><?cs var:msg.email ?><?cs /alt ?></dc:creator>
      <author><?cs alt:msg.author ?><?cs var:msg.email ?><?cs /alt ?></author>
      <dc:date><?cs call:Date.iso8601(msg.date) ?></dc:date>
    </item>
  <?cs /each ?>
</channel>
</rss>
