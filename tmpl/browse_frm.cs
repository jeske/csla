<HTML>
<HEAD>
  <META http-equiv="Content-Type" content="text/html; charset=utf-8">
  <TITLE> Archive: <?cs var:CGI.ArchiveName ?> </TITLE>

<?cs set:extra_path = "" ?>
<?cs set:count = #0 ?>
<?cs each:part = CGI.PathInfo ?>
<?cs if:count > #1 ?>
    <?cs set:extra_path = extra_path + "/" + part ?>
<?cs /if ?>
<?cs set:count = count + #1 ?>
<?cs /each ?>

<SCRIPT LANGUAGE="JavaScript">
<!--
function isDataLoaded() {
  if (document.frames.data.location.href.indexOf("empty") != -1) {
    return false;
  } else {
    return true;
  }
}
//-->
</SCRIPT>

<FRAMESET ROWS="<?cs alt:CGI.List.Header.height ?>30<?cs /alt ?>,*">
  <FRAME frameborder=0 framespacing=0 marginheight=0 marginwidth=0 scrolling=no 
  SRC="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/header?<?cs var:CGI.QueryString ?>">
  <FRAMESET COLS="200,*" frameborder=1 framespacing=1>
    <FRAMESET ROWS="75,*">
      <FRAME frameborder=0 framespacing=0 marginheight=0 marginwidth=0 scrolling=no 
      SRC="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/menu<?cs var:extra_path ?>?<?cs var:CGI.QueryString ?>">
      <FRAME SCROLLING=AUTO frameborder=0 framespacing=0 marginheight=0 marginwidth=0  NAME=index 
      SRC="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/index<?cs var:extra_path ?>?<?cs var:CGI.QueryString ?>">
    </FRAMESET>
    <FRAME frameborder=1 framespacing=2 
           marginheight=0 marginwidth=0
           NAME=data>
  </FRAMESET>
</FRAMESET>
</HEAD>
</HTML>

