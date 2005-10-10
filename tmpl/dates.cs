<?cs if:!?_INCLUDED_DATES ?>
<?cs set: _INCLUDED_DATES = "1" ?>
<?cs def:Date.time(date) ?>
<?cs var:date.hour ?>:<?cs var:date.min ?>&nbsp;<?cs if:#date.am ?>am<?cs else ?>pm<?cs /if ?>
<?cs /def ?>

<?cs def:Date.num_date_time(date) ?>
<?cs var:date.mon ?>-<?cs var:date.mday ?>-<?cs var:date.year ?> <?cs var:date.hour ?>:<?cs var:date.min ?>&nbsp;<?cs if:#date.am ?>am<?cs else ?>pm<?cs /if ?>
<?cs /def ?>

<?cs def:Date.num_date(date) ?>
<?cs var:date.mon ?>-<?cs var:date.mday ?>-<?cs var:date.year ?>
<?cs /def ?>

<?cs def:map_val(val, map) ?><?cs each:item = map ?><?cs if:val == item ?><?cs var:item.val ?><?cs /if ?><?cs /each ?><?cs /def ?>

<?cs def:Date.abbr_name_date(date) ?>
  <?cs call:map_val(date.wday, Lang.Dates.Weekdays_Abbr) ?>,
  <?cs call:map_val(date.mon, Lang.Dates.Months_Abbr) ?> <?cs var:date.mday ?> <?cs var:date.year ?>
<?cs /def ?>

<?cs def:Date.abbr_name_date_time(date) ?>
  <?cs call:Date.abbr_name_date(date) ?> <?cs var:date.hour ?>:<?cs var:date.min ?>&nbsp;<?cs if:#date.am ?>am<?cs else ?>pm<?cs /if ?>
<?cs /def ?>

<?cs def:Date.abbr_short(date) ?>
  <?cs call:map_val(date.mon, Lang.Dates.Months_Abbr) ?> <?cs var:date.mday ?>
<?cs /def ?>

<?cs def:Date.iso8601(date) ?>
<?cs var:date.year ?>-<?cs if:date.mon>#10 ?>0<?cs /if ?><?cs var:date.mon ?>-<?cs var:date.mday ?> <?cs var:date.24hour ?>:<?cs var:date.min ?>:<?cs var:date.sec ?> <?cs var:date.tzoffset ?>
<?cs /def ?>
<?cs /if ?>
