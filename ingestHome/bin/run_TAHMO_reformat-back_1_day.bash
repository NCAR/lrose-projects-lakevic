#!/bin/bash

<<COMMENT
I would run this about 15 minutes after each hour
Set up another to run a 24 hour period at 0Z on 2 days ago
COMMENT

# datestring=`date -u --date='1 days ago' +%Y%m%d%H%M`

start_datestring=`date -u --date='25 hours ago' +%Y-%m-%dT%H:%M`
end_datestring=`date -u --date='24 hours ago' +%Y-%m-%dT%H:%M`

echo
echo "processing data from $start_datestring to $end_datestring"
echo

echo TAHMO_reformat.py \
$RAP_DATA_DIR/$PROJECT/other/TAHMO \
-start_time $start_datestring \
-end_time $end_datestring \
"> $LOG_DIR/TAHMO_reformat-rt.log 2>&1"
echo

TAHMO_reformat.py \
$RAP_DATA_DIR/$PROJECT/other/TAHMO \
-start_time $start_datestring \
-end_time $end_datestring \
> $LOG_DIR/TAHMO_reformat-rt.log 2>&1


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

echo SurfaceAscii2Spdb \
-params $INGEST_HOME/params/SurfaceAscii2Spdb.TAHMO \
-mode ARCHIVE \
-start \"$ingest_start\" \
-end \"$ingest_end\" \
">> $LOG_DIR/reformat_3dPaws-rt.log 2>&1"
echo

SurfaceAscii2Spdb \
-params $INGEST_HOME/params/SurfaceAscii2Spdb.TAHMO \
-mode ARCHIVE \
-start "$ingest_start" \
-end "$ingest_end" \
>> $LOG_DIR/TAHMO_reformat-rt.log 2>&1
