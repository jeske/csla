<?cs include:"dates.cs" ?>
<?cs include:"msg_render.cs" ?>
<?cs include:"header.cs" ?>

<?cs each:msg = CGI.Messages ?>
<?cs call:render_message(msg) ?>
<HR>
<?cs /each ?>

</BODY>
</HTML>
