#!/bin/sh

#システムが準備ができるまで少し待つ。
sleep 10

echo 0 > count

cnt=0

FNAME=`date +%Y%m%d%H%M%S`

#Make Dir
while [ $cnt -le 100 ]
do
    echo ${FNAME}
    if [ -e /home/dsfsb/workarea/log/data_${FNAME} ]; then
        # 存在する場合
        echo "+1"
        FNAME=`date +%Y%m%d%H%M%S`_${cnt}
        cnt=`expr $cnt + 1`
    else
        # 存在しない場合
        echo "create"
        mkdir /home/dsfsb/workarea/log/data_${FNAME}
        mkdir /home/dsfsb/workarea/log/data_${FNAME}/pictures
        break
    fi
done

#start Temperature measurement
/usr/bin/python /home/dsfsb/workarea/python/run_bme280.py > /home/dsfsb/workarea/log/data_${FNAME}/bme280.log &

#start Acceleration measurement
/usr/bin/python /home/dsfsb/workarea/python/run_mpu9250.py > /home/dsfsb/workarea/log/data_${FNAME}/mpu9250.log &
/usr/bin/python /home/dsfsb/workarea/python/run_mpu6050.py > /home/dsfsb/workarea/log/data_${FNAME}/mpu6050.log &

#start move
# sh /home/dsfsb/workarea/sh/get_move.sh data_${FNAME} > /home/dsfsb/workarea/log/data_${FNAME}/get_move.log

#start still
sh /home/dsfsb/workarea/sh/get_still.sh data_${FNAME} > /home/dsfsb/workarea/log/data_${FNAME}/get_still.log

# #start timelapse 
# sh /home/dsfsb/workarea/sh/timelapse.sh data_${FNAME} > /home/dsfsb/workarea/log/data_${FNAME}/timelapse.log &

# #start gps logger
# sh /home/dsfsb/workarea/sh/run_gpxlogger.sh data_${FNAME} &

# #start gpsmon
# gpsmon
