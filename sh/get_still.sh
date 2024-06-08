#!/bin/sh

FNAME=$1
COUNT=`cat count`
OUTPUT_IMAGE="/home/dsfsb/workarea/log/${FNAME}/pictures/img${COUNT}.jpg"

#capture image
libcamera-jpeg -o ${OUTPUT_IMAGE} --nopreview > /home/dsfsb/workarea/log/libcamera.log

#count up
expr `cat count` + 1 > count

