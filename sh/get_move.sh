#!/bin/sh

FNAME=$1
OUTPUT_MOVE="/home/dsfsb/workarea/log/${FNAME}/pictures/video_1080p_30fps.h264" 
OUTPUT_MP4="/home/dsfsb/workarea/log/${FNAME}/pictures/video_1080p_30fps.mp4" 

# Rec Mode 
libcamera-vid -t 3000 --width 1920 --height 1080 --framerate 30 -o ${OUTPUT_MOVE}

# Encode MP4 
# ffmpeg -i ${OUTPUT_MOVE} -c:v copy ${OUTPUT_MP4}



