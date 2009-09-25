<?xml version="1.0" ?>
<?cs include:"dates.cs" ?>
<?cs if:CGI.HTTPS == "on" ?>
  <?cs set:base_url = "https://" + CGI.ServerName ?>
<?cs else ?>
  <?cs set:base_url = "http://" + CGI.ServerName ?>
<?cs /if ?>
<?cs if:CGI.ServerPort != #80 ?>
  <?cs set:base_url = base_url + ":" + CGI.ServerPort ?>
<?cs /if ?>
<?cs set:archive_url = base_url + CGI.URIRoot + CGI.ArchiveName ?>
<rdf:RDF 
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns="http://purl.org/rss/1.0/"
>
<channel rdf:about="<?cs var:base_url ?><?cs var:CGI.RequestURI ?>">
  <title>Archive: <?cs var:CGI.List.Title ?></title>
  <link><?cs var:archive_url ?></link>
  <description><?cs var:html_escape(CGI.List.Description) ?></description>
  <dc:publisher><?cs var:CGI.List.EmailAddress ?></dc:publisher>
  <language><?cs alt:CGI.List.Language ?>en<?cs /alt ?></language>
  <items>
    <rdf:Seq>
      <?cs each:msg = CGI.Messages ?>
        <rdf:li rdf:resource="<?cs var:archive_url ?>/msg/<?cs var:msg.doc_id ?>" />
      <?cs /each ?>
    </rdf:Seq>
  </items>
</channel>
  <?cs each:msg=CGI.Messages ?>
    <item rdf:about="<?cs var:archive_url ?>/msg/<?cs var:msg.doc_id ?>">
      <title><?cs var:html_escape(msg.subject) ?></title>
      <link><?cs var:archive_url ?>/msg/<?cs var:msg.doc_id ?></link>
      <description>
        <?cs var:html_escape(html_strip(msg.summary)) ?>
      </description>
      <dc:creator><?cs alt:msg.author ?><?cs var:msg.email ?><?cs /alt ?></dc:creator>
      <dc:date><?cs call:Date.iso8601(msg.date) ?></dc:date>
    </item>
  <?cs /each ?>
</rdf:RDF>
