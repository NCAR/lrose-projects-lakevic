#!/bin/bash

<<COMMENT
I would run this about 15 minutes after each hour
Set up another to run a 24 hour period at 0Z on 2 days ago
COMMENT

if [[ $# -ne 2 ]] ; then
    echo 'USAGE: run_reformat_3dPaws_interval.bash YYYYMMDDHHMM YYYYMMDDHHMM'
    exit 1
fi

start_datestring=$1
end_datestring=$2

echo
echo "processing data from $start_datestring to $end_datestring"
echo

year=${start_datestring:0:4}
month=${start_datestring:4:2}
day=${start_datestring:6:2}
hour=${start_datestring:8:2}
min=${start_datestring:10:2}
sec="00"
ingest_start="$year $month $day $hour $min $sec"

year=${end_datestring:0:4}
month=${end_datestring:4:2}
day=${end_datestring:6:2}
hour=${end_datestring:8:2}
min=${end_datestring:10:2}
sec="00"
ingest_end="$year $month $day $hour $min $sec"

echo reformat_3dPaws.py \
$RAP_DATA_DIR/$PROJECT/raw/surface/3dPaws \
$RAP_DATA_DIR/$PROJECT/other/3dPaws \
$PROJ_DIR/ingestHome/params/3d-paws_station-locations.txt \
-start_datetime $start_datestring \
-end_datetime $end_datestring \
"> $LOG_DIR/reformat_3dPaws-interval.log 2>&1"
echo

reformat_3dPaws.py \
$RAP_DATA_DIR/$PROJECT/raw/surface/3dPaws \
$RAP_DATA_DIR/$PROJECT/other/3dPaws \
$PROJ_DIR/ingestHome/params/3d-paws_station-locations.txt \
-start_datetime $start_datestring \
-end_datetime $end_datestring \
-debug \
> $LOG_DIR/reformat_3dPaws-interval.log 2>&1

echo SurfaceAscii2Spdb \
-params $INGEST_HOME/params/SurfaceAscii2Spdb.3dPaws \
-mode ARCHIVE \
-start \"$ingest_start\" \
-end \"$ingest_end\" \
">> $LOG_DIR/reformat_3dPaws-interval.log 2>&1"
echo

SurfaceAscii2Spdb \
-params $INGEST_HOME/params/SurfaceAscii2Spdb.3dPaws \
-mode ARCHIVE \
-start "$ingest_start" \
-end "$ingest_end" \
>> $LOG_DIR/reformat_3dPaws-interval.log 2>&1
