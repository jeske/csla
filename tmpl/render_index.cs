<STYLE>
A.subj:link { color:black; text-decoration:none;  }
A.subj:visited { color:black; text-decoration:none;; }
A.subj:hover { color:black; text-decoration:none;  }
A.subj:active { color:black; text-decoration:none; }

</STYLE>
<script language="JavaScript1.2">
<!--

<?cs include:"js_common.cs" ?>

var Pages = new Array();
<?cs each:page = CGI.Index.MsgPage ?>
Pages['<?cs name:page ?>'] = [<?cs var:page ?>];
<?cs /each ?>

var CurrentPage = 0;

<?cs if:CGI.PathInfo.2 == "thread" ?>
  <?cs set:Activate.doc_id = CGI.PathInfo.4 ?>
  <?cs set:Activate.thread_id = CGI.PathInfo.3 ?>
<?cs /if ?>

var FirstPage = null;
var FirstDoc = null;
var FirstURL = null;

<?cs set:found_first = #0 ?>

<?cs def:walk_tree(tree) ?>
<?cs each:msg = tree ?>
  <?cs if:?Activate.doc_id ?>
    <?cs if:msg.doc_id == Activate.doc_id ?>
      FirstPage = '<?cs var:msg.page ?>';
      FirstDoc  = '<?cs var:msg.doc_id ?>';
      FirstURL = "<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/messages/<?cs var:CGI.Index.MsgPage[msg.page] ?>?view=<?cs var:CGI.IndexMode ?>&noheader=1#doc_<?cs var:msg.doc_id ?>";
    <?cs /if ?>
  <?cs else ?>
    <?cs if:found_first == #0 ?>
      <?cs set:found_first = #1 ?>
      FirstPage = '<?cs var:msg.page ?>';
      FirstDoc  = '<?cs var:msg.doc_id ?>';
      FirstURL = "<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/messages/<?cs var:CGI.Index.MsgPage[msg.page] ?>?view=<?cs var:CGI.IndexMode ?>&noheader=1#doc_<?cs var:msg.doc_id ?>";
    <?cs /if ?>
  <?cs /if ?>
  <?cs call:walk_tree(msg.children) ?>
<?cs /each ?>
<?cs /def ?>
<?cs if:CGI.DisplayMode == "thread" ?>
  <?cs call:walk_tree(CGI.Index.Threads) ?>
<?cs else ?>
  <?cs call:walk_tree(CGI.Index.Messages) ?>
<?cs /if ?>


function I_trigger_current_docid(doc_id) {
  select_page(CurrentPage,doc_id);
}

function select_page(page, doc_id) {
  if (page != CurrentPage) {
    for (var x = 0; x < Pages[CurrentPage].length; x++)
    {
      document.getElementById("ind_" + Pages[CurrentPage][x]).src = "/discuss/tmpl/img/blanktri.gif";
    }
    CurrentPage = page;
  }
  var elem_docid;
  for (var x = 0; x < Pages[page].length; x++)
  {
    elem_docid = Pages[page][x];
    if (Pages[page][x] == parseInt(doc_id)) {
      document.getElementById("ind_" + elem_docid).src = "/discuss/tmpl/img/tri.gif";
    } else {
     <?cs if:#CGI.Prefs.MultiMsg ?>
      document.getElementById("ind_" + elem_docid).src = "/discuss/tmpl/img/bartri.gif";
     <?cs else ?>
      document.getElementById("ind_" + elem_docid).src = "/discuss/tmpl/img/blanktri.gif";
     <?cs /if ?>
    }
  }

  // document.getElementById("spc_" + page).src = "/discuss/tmpl/img/bartri.gif";
}

function setup() {
  if (TargetFrame) {
    select_page(FirstPage,FirstDoc);
    var url;

    <?cs if:#CGI.Prefs.MultiMsg ?>
      url = FirstURL;
    <?cs else ?>
      url = "<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/messages/" + FirstDoc + "?noheader=1";
    <?cs /if ?>
    TargetFrame.location.replace(url);
  }

//  if (parent && parent.isDataLoaded && parent.frames && parent.frames.data && FirstPage) {
//      select_page(FirstPage,FirstDoc);
//      parent.frames.data.location.replace(FirstURL);
//  }
}

-->
</script>


<?cs def:render_msg_link(msg) ?>
 <?cs if:#CGI.Prefs.MultiMsg ?>
  <a <?cs call:msgclass(msg) ?> onClick="select_page('<?cs var:msg.page ?>', '<?cs var:msg.doc_id ?>');" target=data href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/messages/<?cs var:CGI.Index.MsgPage[msg.page] ?>?mode=<?cs var:CGI.IndexMode ?>&noheader=1#doc_<?cs var:msg.doc_id ?>"><?cs var:post_count ?> <?cs alt:msg.author ?><?cs var:msg.email ?><?cs /alt ?></a>
 <?cs else ?>
  <a <?cs call:msgclass(msg) ?> onClick="select_page('<?cs var:msg.page ?>', '<?cs var:msg.doc_id ?>');" target=data href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/messages/<?cs var:msg.doc_id ?>?noheader=1"><?cs var:post_count ?> <?cs alt:msg.author ?><?cs var:msg.email ?><?cs /alt ?></a>
 <?cs /if ?>
<?cs /def ?>

<?cs def:render_msg_link_author(msg) ?>
 <a <?cs call:msgclass(msg) ?> onClick="select_page('<?cs var:msg.page ?>', '<?cs var:msg.doc_id ?>');" target=data href="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/messages/<?cs var:CGI.Index.MsgPage[msg.page] ?>?mode=<?cs var:CGI.IndexMode ?>&noheader=1#doc_<?cs var:msg.doc_id ?>"><?cs var:post_count ?> <?cs var:msg.subject ?></a> 
<?cs /def ?>

<?cs set:markedfirstlink=#0 ?>

<?cs def:render_thread(msg, prefix) ?>
  <?cs set:post_count = post_count + #1 ?>
  <?cs if:CUR_SUBJECT != msg.subject_reduced ?>
    <?cs set:CUR_SUBJECT = msg.subject_reduced ?>
    <tt><?cs var:prefix ?></tt><b><A HREF="#" CLASS=subj TITLE="<?cs var:msg.subject ?>"><?cs var:msg.subject ?></A></b><br>
  <?cs /if ?>
  <img alt="" ID="ind_<?cs var:msg.doc_id ?>" width=8 height=10 src="/discuss/tmpl/img/blanktri.gif"><tt><?cs var:prefix ?></tt> <?cs call:render_msg_link(msg) ?> <?cs call:Date.abbr_short(msg.date) ?><br>
  <?cs each:sub = msg.children ?>
    <?cs call:render_thread(sub, prefix + "&nbsp;") ?>
  <?cs /each ?>
<?cs /def ?>

<NOBR>
<font face=arial,sans-serif size=-1>
<?cs if:CGI.DisplayMode == "thread" ?>
  <?cs each:msg = CGI.Index.Threads ?>
    <?cs set:post_count = #0 ?>
    <?cs call:render_thread(msg, "") ?>
  <?cs /each ?>
<?cs elif:CGI.DisplayMode == "author" ?>
  <b><A HREF="#" CLASS=subj TITLE="<?cs alt:CGI.Author.Name ?><?cs var:CGI.Author.Email ?><?cs /alt ?>"><?cs alt:CGI.Author.Name ?><?cs var:CGI.Author.Email ?><?cs /alt ?></A></b><br>
  <?cs set:post_count = #0 ?>
  <?cs each:msg = CGI.Index.Messages ?>
    <?cs set:post_count = post_count + #1 ?>
    <img alt="" ID="ind_<?cs var:msg.doc_id ?>" width=8 height=10 src="/discuss/tmpl/img/blanktri.gif"><tt><?cs var:prefix ?></tt> <?cs call:render_msg_link_author(msg) ?> <?cs call:Date.abbr_short(msg.date) ?><br>
  <?cs /each ?>
<?cs /if ?>
</font>
</NOBR>
