<?cs include:"header.cs" ?>
<p>

<table align=center>
<form method="<?cs var:CGI.URIRoot ?><?cs var:CGI.ArchiveName ?>/timezone">
<tr>
  <td valign=top>Select a TimeZone:</td>
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
<td><input type=submit name="Action.SetTimezone" value="Set"></td>
</tr>
<tr><td colspan=2 align=center>
Default for list is <?cs var:CGI.List.TimeZone ?>.
</td></tr>
</form>
</table>

<?cs include:"footer.cs" ?>
