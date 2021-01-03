#!/bin/sh

FNAME=$1
COUNT=`cat count`
OUTPUT_IMAGE=`printf "/home/pi/workarea/log/${FNAME}/pictures/img%08d.jpg" ${COUNT}`

#capture image
raspistill -o ${OUTPUT_IMAGE} -w 1920 -h 1080 -t 3000

#count up
expr `cat count` + 1 > count

