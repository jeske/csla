<?cs include:"header.cs" ?>
<p>

<table width=80% align=center>
<TR><TD BGCOLOR=<?cs var:Style.TitleBarColor ?> CLASS=navi0>Preferences</TD></TR>
<TR><TD>
<table align=center>
<form method="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/prefs">
<tr>
  <td valign=top align=right><b>Select a TimeZone:</b></td>
  <td><SELECT NAME=timezone SIZE=10>
          <OPTION VALUE="default"> Default
	  <OPTION VALUE="GMT" <?cs if:Cookie.TZ=="GMT" ?>SELECTED<?cs /if ?>>GMT
	  <?cs each:tz1=Timezones ?> 
	    <?cs each:tz2=tz1 ?>
	      <OPTION VALUE="<?cs var:tz2 ?>" <?cs if:tz2==Cookie.TZ ?>SELECTED<?cs /if ?>><?cs var:tz2 ?>
	    <?cs /each ?>
	  <?cs /each ?>
	</SELECT>
  </td>
</tr>
<tr><td colspan=2 align=center>
Default for list is <i><?cs var:CGI.List.TimeZone ?></i>.
</td></tr>
<tr><td>&nbsp;</td></tr>


<tr>
  <td valign=top align=right><b>Select Read Status Key:</b></td>
  <td><input type=text size=40 name="whichread_key" value="<?cs var:Cookie.WRID ?>">
  </td>
</tr>
<tr><td colspan=2 align=center>

This value is used to store server-side information about
which posts you've read. If you use the same key for two hosts, those
two hosts will share read-status. We've randomly generated a key for
you, but one easy-to-remember key is your email address. If you are privacy concious
just make something up.

</td></tr>
<tr><td>&nbsp;</td></tr>

<tr>
  <td valign=top align=right><b>Select Browse Style:</b></td>
  <td>
      <input type=radio name=browse_style value="frame" <?cs if:CGI.Prefs.Browse == "frame" ?>CHECKED<?cs /if ?>>Frames<br>
      <input type=radio name=browse_style value="iframe" <?cs if:CGI.Prefs.Browse == "iframe" ?>CHECKED<?cs /if ?>>IFrame<br>
      <input type=radio name=browse_style value="noframes" <?cs if:CGI.Prefs.Browse == "noframes" ?>CHECKED<?cs /if ?>>No Frames<br>
  </td>
</tr>


<tr><td>&nbsp;</td></tr>
<tr>
  <td valign=top align=right><b>In Frames/IFrame mode:</b></td>
  <td>
    <input type=checkbox name=multi_msg value="1" <?cs if:#CGI.Prefs.MultiMsg ?>CHECKED<?cs /if ?>> Multiple messages in frame
  </td>
</tr>
<tr>
  <td colspan=2 align=center><input type=submit name="Action.SetPrefs" value="Set Preferences"></td>
</tr>
</form>
</table>
</td></tr></table>

<?cs include:"footer.cs" ?>
