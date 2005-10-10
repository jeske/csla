<?cs include:"dates.cs" ?>
<?cs include:"header.cs" ?>
<STYLE>
A.subj:link { color:black; text-decoration:none; cursor:default; }
A.subj:visited { color:black; text-decoration:none; cursor:default; }
A.subj:hover { color:black; text-decoration:none; cursor:default; }
A.subj:active { color:black; text-decoration:none; cursor:default; }

</STYLE>

<?cs def:render_thread(msg, prefix) ?>
  <?cs set:post_count = post_count + #1 ?>
  <?cs if:CUR_SUBJECT != msg.subject_reduced ?>
    <?cs set:CUR_SUBJECT = msg.subject_reduced ?>
    <tt><?cs var:prefix ?></tt><b><?cs var:msg.subject ?></b><br>
  <?cs /if ?>
  <tt><?cs var:prefix ?></tt><a <?cs call:msgclass(msg) ?> href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/msg/<?cs var:msg.doc_id ?>"><?cs var:post_count ?> <?cs alt:msg.author ?><?cs var:msg.email ?><?cs /alt ?></a> <?cs call:Date.abbr_short(msg.date) ?><br>
  <?cs each:sub = msg.children ?>
    <?cs call:render_thread(sub, prefix + "&nbsp;") ?>
  <?cs /each ?>
<?cs /def ?>

<BLOCKQUOTE>
<NOBR>
<font face=arial,sans-serif size=-1>
<?cs if:CGI.DisplayMode == "thread" ?>
  <?cs each:msg = CGI.Index.Threads ?>
    <?cs set:post_count = #0 ?>
    <?cs call:render_thread(msg, "") ?>
  <?cs /each ?>
<?cs elif:CGI.DisplayMode == "author" ?>
  <b><?cs alt:CGI.Author.Name ?><?cs var:CGI.Author.Email ?><?cs /alt ?></b><br>
  <?cs set:post_count = #0 ?>
  <?cs each:msg = CGI.Index.Messages ?>
    <?cs set:post_count = post_count + #1 ?>
    <tt><?cs var:prefix ?></tt><a  <?cs call:msgclass(msg) ?> href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/msg/<?cs var:msg.doc_id ?>"><?cs var:post_count ?> <?cs var:msg.subject ?></a> <?cs call:Date.abbr_short(msg.date) ?><br>
  <?cs /each ?>
<?cs /if ?>
</font>
</NOBR>
</BLOCKQUOTE>

<?cs include:"footer.cs" ?>


