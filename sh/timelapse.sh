#!/bin/sh

echo 0 > count

FNAME=$1

for i in `seq 1 99999`
do
  sh /home/pi/workarea/sh/get_still.sh ${FNAME}  && sleep 1
done

