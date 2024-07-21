#!/bin/sh
FNAME=$1

# Rec Mode 
libcamera-vid -t 600000 --codec mjpeg --segment 1000 -n -o /home/dsfsb/workarea/log/${FNAME}/pictures/videotest%d.jpg

