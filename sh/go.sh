#!/bin/sh

echo 0 > count

cnt=0

FNAME=`date +%Y%m%d%H%M%S`

#Make Dir
while [ $cnt -le 100 ]
do
    echo ${FNAME}
    if [ -e /home/pi/workarea/log/data_${FNAME} ]; then
        # 存在する場合
        echo "+1"
        FNAME=`date +%Y%m%d%H%M%S`_${cnt}
        cnt=`expr $cnt + 1`
    else
        # 存在しない場合
        echo "create"
        mkdir /home/pi/workarea/log/data_${FNAME}
        mkdir /home/pi/workarea/log/data_${FNAME}/pictures
        break
    fi
done

#start Temperature measurement
python /home/pi/workarea/python/run_bme280.py > /home/pi/workarea/log/data_${FNAME}/bme280.log &

#start Acceleration measurement
# python /home/pi/workarea/python/run_mpu9250.py > /home/pi/workarea/log/data_${FNAME}/mpu9250.log &
python /home/pi/workarea/python/run_mpu6050.py > /home/pi/workarea/log/data_${FNAME}/mpu6050.log &

#start gps logger
sh /home/pi/workarea/sh/run_gpxlogger.sh data_${FNAME} &

#start timelapse 
sh /home/pi/workarea/sh/timelapse.sh data_${FNAME} &

#start gpsmon
gpsmon
