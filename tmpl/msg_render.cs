<?cs def:display_body(m,doc_id) ?>
  <?cs each:sub = m.parts ?>
    <?cs if:sub.h_from ?>
     <TABLE STYLE="font-size:10pt" BORDER=0 CELLSPACING=1 CELLPADDING=0 BGCOLOR=<?cs var:Style.CellBGColor ?>>
      <TR><TD WIDTH=1% VALIGN=TOP ALIGN=RIGHT><B>From:</B></TD>
          <TD VALIGN=TOP > <?cs var:sub.h_from ?> </TD></TR>
      <TR><TD VALIGN=TOP ALIGN=RIGHT><B>To:</B></TD>
          <TD> <?cs var:sub.h_to ?> </TD></TR>
<?cs if:sub.h_cc ?>
      <TR><TD VALIGN=TOP ALIGN=RIGHT><B>Cc:</B></TD>
          <TD> <?cs var:sub.h_cc ?> </TD></TR>
<?cs /if ?>
      <TR><TD VALIGN=TOP ALIGN=RIGHT><B>Date:</B></TD>
          <TD> <?cs var:sub.h_date ?> </TD></TR>
      <?cs if:sub.h_date.sec ?>
	<TR><TD VALIGN=TOP ALIGN=RIGHT><B>Local:</B></TD>
	    <TD> <?cs call:Date.abbr_name_date_time(sub.h_date) ?> </TD></TR>
      <?cs /if ?>
      <TR><TD VALIGN=TOP ALIGN=RIGHT><B>Subject:</B></TD>
          <TD VALIGN=TOP> <?cs var:sub.h_subject ?> </TD></TR>
     </TABLE>
    <?cs /if ?>

    <?cs set:attach_url = CGI.URIRoot + CGI.ArchiveName + "/attach/" + 
              doc_id + "/" + sub.num + ":" + sub.name ?>


    <?cs if:sub.b_type == "multipart" ?>
      <?cs call:display_body(sub,doc_id) ?>
    <?cs elif:sub.b_type == "message" ?>
      <P>
      [ Attached Message ]<BR>
      <?cs call:display_body(sub,doc_id) ?>

    <?cs elif:sub.b_type == "attach" ?>

      <P>
      [ Attachment #<?cs name:sub ?>: <a target=_top href="<?cs var:attach_url ?>"><?cs var:sub.name ?></a> ]<br>
    <?cs elif:sub.b_type == "image" ?>
      <P>
      [ Attachment #<?cs name:sub ?>: <a target=_top href="<?cs var:attach_url ?>"><?cs var:sub.name ?></a> ]<br>
      <a target=_top href="<?cs var:attach_url ?>">
        <img width=150 src="<?cs var:attach_url ?>">
      </a>
    <?cs else ?>
      <?cs if:sub.name ?>
      <p>
      [ Attachment #<?cs name:sub ?>: <a target=_top href="<?cs var:attach_url ?>"><?cs var:sub.name ?></a> ]<br>
      <?cs /if ?>
      <?cs var:sub.body ?>
    <?cs /if ?>
  <?cs /each ?>
<?cs /def ?>

<?cs def:render_attach_list(m) ?>
  <?cs each:sub = m.parts ?>
    <?cs if:sub.b_type == "multipart" ?>
      <?cs call:render_attach_list(sub) ?>
    <?cs elif:sub.b_type == "message" ?>
      <?cs call:render_attach_list(sub) ?>
    <?cs elif:sub.b_type == "attach"  || sub.b_type == "image" ?>
      <IMG WIDTH=10 HEIGHT=12 BORDER=0 SRC="<?cs var:CGI.ScriptName ?>/tmpl/img/ui/r/unknown_file_icon.gif">&nbsp;<a target=_top href="/cgi-bin/attach.py/<?cs var:sub.name ?>?boxid=<?cs var:Query.boxid ?>&cur=<?cs var:Query.cur ?>&idx_cur=<?cs var:Query.idx_cur ?>&attach=<?cs name:sub ?>:<?cs var:sub.name ?>"><?cs var:sub.name ?></a>&nbsp;
    <?cs /if ?>
  <?cs /each ?>
<?cs /def ?>

<?cs # ----------------------------------------------------------------------- ?>

<?cs def:render_message(msg,full_msg) ?>

<?cs if:Query.dmode != "source" ?>
<TABLE WIDTH=100% BORDER=0 CELLSPACING=0 CELLPADDING=2 BGCOLOR=<?cs var:Style.CellBGColor ?>>
<TR><TD CLASS=hdr WIDTH=1% VALIGN=TOP ALIGN=RIGHT><b>From:</b></TD>
    <TD> <?cs var:msg.h_from ?> </TD> 
    <TD WIDTH=1% VALIGN=TOP ROWSPAN=3 NOWRAP> 
      <?cs if: (Query.view != "thread") && (#full_msg.Meta.thread_count > #1) ?>
      <A TARGET=_top HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/thread/<?cs var:full_msg.Meta.thread_id ?>/<?cs var:full_msg.Meta.doc_id ?>">View Thread (<?cs var:full_msg.Meta.thread_count ?> posts)</A><br>
      <?cs /if ?>
      <?cs if:Query.view != "author" ?>
      <A TARGET=_top HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/<?cs var:CGI.BrowseUri ?>/author/<?cs var:url_escape(full_msg.Meta.email) ?>/<?cs var:full_msg.Meta.doc_id ?>">View Author</A><br>
      <?cs /if ?>
      <?cs if:CGI.PathInfo.1 != "msg" ?>
        <A TARGET=_top HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/msg/<?cs var:full_msg.Meta.doc_id ?>">View This Message</A><br>
      <?cs /if ?>
      <?cs if:Query.dmode != "source" && CGI.PathInfo.1 == "msg" ?>
        <A TARGET=_top HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/msg/<?cs var:full_msg.Meta.doc_id ?>?dmode=source">View Source</A><br>
      <?cs /if ?>
    </TD>
</TR>


<TR><TD VALIGN=TOP CLASS=hdr ALIGN=RIGHT><b>Date:</b></TD>
    <TD> <?cs var:msg.h_date ?></TD>

    </TR>

<?cs if:msg.h_date.sec ?>
  <TR><TD CLASS=hdr ALIGN=RIGHT><B>Local:</B></TD>
      <TD> <?cs call:Date.abbr_name_date_time(msg.h_date) ?> </TD></TR>
<?cs /if ?>
<TR><TD CLASS=hdr VALIGN=TOP ALIGN=RIGHT><b>Subject:</b></TD>
    <TD COLSPAN=2 WIDTH=99%><font size=-1><b><?cs var:msg.h_subject ?></b></TD></TR>
</TABLE>

<p>
<div style="font-size:10pt;margin:0px 0px 0px 20px;">
<?cs if:msg.b_type == "multipart" ?>
  <?cs call:display_body(msg,full_msg.Meta.doc_id) ?>
<?cs else ?>
  <?cs var:msg.body ?>
<?cs /if ?>
</div>

&nbsp;<br>

<?cs else ?>  <?cs # --- Query.dmode != "source" ?>

<TABLE WIDTH=100% BORDER=0 CELLSPACING=0 CELLPADDING=2 BGCOLOR=<?cs var:Style.CellBGColor ?>>
<TR><TD ALIGN=CENTER>
<A TARGET=_top HREF="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/msg/<?cs var:full_msg.Meta.doc_id ?>">View Parsed</A><br>
</TD></TR>
</TABLE>

<pre>
<?cs var:html_escape(msg.RAWDATA) ?>
</PRE>

<?cs /if ?> <?cs # --- /if Query.dmode == "source" ?>


<?cs /def ?>
