#!/bin/bash

<<COMMENT
I would run this about 15 minutes after each hour
Set up another to run a 24 hour period at 0Z on 2 days ago
COMMENT

# datestring=`date -u --date='1 days ago' +%Y%m%d%H%M`

start_datestring=`date -u --date='4 hours ago' +%Y-%m-%dT%H:%M`
end_datestring=`date -u --date='now' +%Y-%m-%dT%H:%M`

echo
echo "processing data from $start_datestring to $end_datestring"
echo

year=${start_datestring:0:4}
month=${start_datestring:5:2}
day=${start_datestring:8:2}
hour=${start_datestring:11:2}
min=${start_datestring:14:2}
sec="00"
ingest_start="$year $month $day $hour $min $sec"

year=${end_datestring:0:4}
month=${end_datestring:5:2}
day=${end_datestring:8:2}
hour=${end_datestring:11:2}
min=${end_datestring:14:2}
sec="00"
ingest_end="$year $month $day $hour $min $sec"

echo Metar2Spdb \
-params $INGEST_HOME/params/Metar2Spdb.AWS \
-mode ARCHIVE \
-start \"$ingest_start\" \
-end \"$ingest_end\" \
"> $LOG_DIR/Metar2Spdb.AWS.log 2>&1"
echo

Metar2Spdb \
-params $INGEST_HOME/params/Metar2Spdb.AWS \
-mode ARCHIVE \
-start "$ingest_start" \
-end "$ingest_end" \
>> $LOG_DIR/Metar2Spdb.AWS.log 2>&1
