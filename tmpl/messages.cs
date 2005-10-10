<?cs include:"dates.cs" ?>
<?cs include:"msg_render.cs" ?>
<?cs include:"header.cs" ?>
<SCRIPT LANGUAGE="JavaScript">
<!--
<?cs include:"js_common.cs" ?>

var AnchorLocs = new Array();
var ActiveDocId = 0;
var gotFirstScroll = 0;

function computeLoc(doc_id) {
  if (! IS_IE ) { return; }

  var offsetobj =  document.getElementById("a_" + doc_id);
  
  if (offsetobj.clientTop != null) {
    offset = 0;
    loffset = 0;
    while (offsetobj) {
      offset += offsetobj.offsetTop + offsetobj.clientTop;
      loffset += offsetobj.offsetLeft + offsetobj.clientLeft;
      offsetobj = offsetobj.offsetParent;
    }
  }
  var o = new Object();
  o.doc_id = doc_id;
  o.offset = offset;

  AnchorLocs[AnchorLocs.length] = o;
}

function setup() {
  <?cs each:msg = CGI.Messages ?>
    computeLoc('<?cs var:msg.Meta.doc_id ?>');
  <?cs /each ?>

  window.onscroll = onScrollHandler;  
}

function onScrollHandler(e) {
  if (gotFirstScroll == 0) {
    gotFirstScroll = 1;
    return;
  }
  setTimeout(processScroll,10);
}

function processScroll() {
  
  var cur_loc = scrollLoc();

  var nearest_docid = 0;
  var nearest_delta = -1;

  var delta;
  for (x=0;x<AnchorLocs.length;x++) {
    delta = Math.abs(AnchorLocs[x].offset - cur_loc);
    if ((nearest_delta == -1) || (delta < nearest_delta)) {
      if ((cur_loc + 200) > AnchorLocs[x].offset) {
        nearest_delta = delta;
        nearest_docid = AnchorLocs[x].doc_id;
      }
    }
  }

  if (ActiveDocId != nearest_docid) {
     ActiveDocId = nearest_docid;
     trigger_current_docid(nearest_docid);
  }
  
}

function trigger_current_docid(docid) {
  if (parent.frames && parent.frames.index) {
    if (parent.frames.index.I_trigger_current_docid) {
      parent.frames.index.I_trigger_current_docid(docid);
    }
  }
}

//-->
</SCRIPT>

<STYLE>
td { font-family:"Arial,Helvetica,sans-serif";}
td.hdr { background:<?cs var:Style.Msg.HeaderBGColor ?>; color:white; }
</STYLE>

<?cs each:msg = CGI.Messages ?>
<a ID="a_<?cs var:msg.Meta.doc_id ?>" name="doc_<?cs var:msg.Meta.doc_id ?>"></a>
<?cs call:render_message(msg.Message,msg) ?>
<?cs /each ?>

<SCRIPT LANGUAGE="JavaScript">
<!--
setup();
//-->
</SCRIPT>

</BODY>
</HTML>
