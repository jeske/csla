<?cs if:!UTL_CODE_JS_INCLUDE ?>
<?cs set:UTL_CODE_JS_INCLUDE="included" ?>

// ----------------------------------
// cross-browser functions

var IE_all_cache = new Object();
function IE_getElementById(id) {
  if (IE_all_cache[id] == null) {
    IE_all_cache[id] = document.all[id];
  }
  return IE_all_cache[id];
}

if (document.all) {
  // IE < 6.0 needs this...
  document.getElementById = IE_getElementById;
  IS_IE = 1;
} else {
  IS_IE = 0;
}


function scrollLoc() {
  if (document.all) {
    return window.document.body.scrollTop;
  } else {
    return window.pageYOffset;
  }
}


function toggleQDisplay(div_id) {
  var adiv = document.getElementById(div_id);

  if (adiv == null || adiv.style == null) {
    alert("missing div toggle: " + div_id);
    return;
  }

  if (adiv.style.display == "none") {
    adiv.style.display = "block";
  } else {
    adiv.style.display = "none";
  }
}


<?cs /if ?>
