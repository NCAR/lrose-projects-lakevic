#!/bin/bash

<<COMMENT
I would run this about 15 minutes after each hour
Set up another to run a 24 hour period at 0Z on 2 days ago
COMMENT

# datestring=`date -u --date='1 days ago' +%Y%m%d%H%M`

start_datestring=`date -u --date='49 hours ago' +%Y-%m-%dT%H:%M`
end_datestring=`date -u --date='48 hours ago' +%Y-%m-%dT%H:%M`

echo $start_datestring
echo $end_datestring

echo archive_image_dump.py $start_datestring $end_datestring CIDD.surfaceDataImgDumpArchive -debug
archive_image_dump.py $start_datestring $end_datestring CIDD.surfaceDataImgDumpArchive -debug
