#!/usr/bin/env python
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
import time
import threading
import signal
import sys

import smbus2
import qwiic_icm20948
import serial
import pynmea2

import csv

bme280_condition   = threading.Condition()
mpu6050_condition  = threading.Condition()
icm20948_condition = threading.Condition()
imx219_condition   = threading.Condition()

BME280_ADDR  = 0x76
MPU6050_ADDR = 0x68
PWR_MGMT_1   = 0x6B
ACCEL_XOUT_H = 0x3B

imu          = qwiic_icm20948.QwiicIcm20948( address=0x68 )
bus3         = smbus2.SMBus(3)
bus4         = smbus2.SMBus(4)
imu.begin()

running       = True
bme280Ready   = False
mpu6050Ready  = False
imx219Ready   = False
icm20948Ready = False
frame_count   = 0
frame_ready     = threading.Event()

def generate_empty_csvFile( csvFileName , data ):
    print("[Info] Create the  " + csvFileName + ".")
    fopen  = open( csvFileName , 'w' , newline='' , encoding='utf-8' )
    writer = csv.writer( fopen )
    writer.writerows( data )
    fopen.close()

def get_csvFile( csvFileName ):
    fappend = open( csvFileName , 'a' , newline='' , encoding='utf-8' , buffering=65536 )
    return fappend

generate_empty_csvFile(
    "icm20948.csv" ,
    [
        [
            'elapsed_time',
            'start_epoch_time',
            'unix_epoch_time',
            'ax',
            'ay',
            'az',
            'gx',
            'gy',
            'gz',
            'mx',
            'my',
            'mz',
            'temp'
        ]
    ]
)

generate_empty_csvFile(
    "mpu6050.csv" ,
    [
        [
            'elapsed_time'     ,
            'start_epoch_time' ,
            'unix_epoch_time'  ,
            'mpu6050_data[0]'  ,
            'mpu6050_data[1]'  ,
            'mpu6050_data[2]'  ,
            'mpu6050_data[3]'  ,
            'mpu6050_data[4]'  ,
            'mpu6050_data[5]'  ,
            'mpu6050_data[6]'  ,
            'mpu6050_data[7]'  ,
            'mpu6050_data[8]'  ,
            'mpu6050_data[9]'  ,
            'mpu6050_data[10]' ,
            'mpu6050_data[11]' ,
            'mpu6050_data[12]' ,
            'mpu6050_data[13]'
        ]
    ]
)

generate_empty_csvFile(
    "bme280.csv" ,
    [
        [
            'elapsed_time'     ,
            'start_epoch_time' ,
            'unix_epoch_time'  ,
            'read24byte[0]'    ,
            'read24byte[1]'    ,
            'read24byte[2]'    ,
            'read24byte[3]'    ,
            'read24byte[4]'    ,
            'read24byte[5]'    ,
            'read24byte[6]'    ,
            'read24byte[7]'    ,
            'read24byte[8]'    ,
            'read24byte[9]'    ,
            'read24byte[10]'   ,
            'read24byte[11]'   ,
            'read24byte[12]'   ,
            'read24byte[13]'   ,
            'read24byte[14]'   ,
            'read24byte[15]'   ,
            'read24byte[16]'   ,
            'read24byte[17]'   ,
            'read24byte[18]'   ,
            'read24byte[19]'   ,
            'read24byte[20]'   ,
            'read24byte[21]'   ,
            'read24byte[22]'   ,
            'read24byte[23]'   ,
            'read1Byte0xA1'    ,
            'read7byte[0]'     ,
            'read7byte[1]'     ,
            'read7byte[2]'     ,
            'read7byte[3]'     ,
            'read7byte[4]'     ,
            'read7byte[5]'     ,
            'read7byte[6]'     ,
            'read8byte[0]'     ,
            'read8byte[1]'     ,
            'read8byte[2]'     ,
            'read8byte[3]'     ,
            'read8byte[4]'     ,
            'read8byte[5]'     ,
            'read8byte[6]'     ,
            'read8byte[7]'
        ]
    ]
)

generate_empty_csvFile(
    "imx219.csv" ,
    [
        [
            'elapsed_time'     ,
            'start_epoch_time' ,
            'unix_epoch_time'  ,
        ]
    ]
)

icm20948CsvFile = get_csvFile("icm20948.csv")
bme280CsvFile   = get_csvFile("bme280.csv")
mpu6050CsvFile  = get_csvFile("mpu6050.csv")
imx219CsvFile   = get_csvFile("imx219.csv")

icm20948CsvFileWriter = csv.writer( icm20948CsvFile )
mpu6050CsvFileWriter  = csv.writer( mpu6050CsvFile   )
bme280CsvFileWriter   = csv.writer( bme280CsvFile  )
imx219CsvFileWriter   = csv.writer( imx219CsvFile   )

def signal_handler(sig, frame):
    global running
    global icm20948CsvFile
    global bme280CsvFile
    global mpu6050CsvFile
    global imx219CsvFile
    icm20948CsvFile.close()
    bme280CsvFile.close()
    mpu6050CsvFile.close()
    imx219CsvFile.close()
    print("\nCtrl+C detected. Stopping recording...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def imx219_consumer():
    global imx219Ready
    start = time.time()
    global imx219CsvFileWriter
    while running:
        imx219_condition.acquire()
        while not imx219Ready:
            imx219_condition.wait()
        imx219_condition.release()
        end = time.time()
        current_total_time = end-start
        data = [
            [
                current_total_time ,
                start              ,
                end
            ]
        ]
        imx219CsvFileWriter.writerows(data)
        imx219Ready = False

def bme280_consumer():
    global bme280Ready
    global bme280CsvFileWriter
    start = time.time()
    while running:
        bme280_condition.acquire()
        while not bme280Ready:
            bme280_condition.wait()
        bme280_condition.release()
        bus4.write_byte_data(BME280_ADDR, 0xF2, 0x01)  # Humidity oversampling x1                   
        bus4.write_byte_data(BME280_ADDR, 0xF4, 0x27)  # Normal mode, temp/press oversampling x1    
        bus4.write_byte_data(BME280_ADDR, 0xF5, 0xA0)  # Config                                     
        read24byte    = bus4.read_i2c_block_data ( BME280_ADDR , 0x88 , 24 )
        read1Byte0xA1 = bus4.read_byte_data      ( BME280_ADDR , 0xA1      )
        read7byte     = bus4.read_i2c_block_data ( BME280_ADDR , 0xE1 ,  7 )
        read8byte     = bus4.read_i2c_block_data ( BME280_ADDR , 0xF7 ,  8 )
        end                = time.time()
        current_total_time = end-start
        data = [
            [
                current_total_time ,
                start              ,
                end                ,
                read24byte[0]      ,
                read24byte[1]      ,
                read24byte[2]      ,
                read24byte[3]      ,
                read24byte[4]      ,
                read24byte[5]      ,
                read24byte[6]      ,
                read24byte[7]      ,
                read24byte[8]      ,
                read24byte[9]      ,
                read24byte[10]     ,
                read24byte[11]     ,
                read24byte[12]     ,
                read24byte[13]     ,
                read24byte[14]     ,
                read24byte[15]     ,
                read24byte[16]     ,
                read24byte[17]     ,
                read24byte[18]     ,
                read24byte[19]     ,
                read24byte[20]     ,
                read24byte[21]     ,
                read24byte[22]     ,
                read24byte[23]     ,
                read1Byte0xA1      ,
                read7byte[0]       ,
                read7byte[1]       ,
                read7byte[2]       ,
                read7byte[3]       ,
                read7byte[4]       ,
                read7byte[5]       ,
                read7byte[6]       ,
                read8byte[0]       ,
                read8byte[1]       ,
                read8byte[2]       ,
                read8byte[3]       ,
                read8byte[4]       ,
                read8byte[5]       ,
                read8byte[6]       ,
                read8byte[7]
            ]
        ]
        bme280CsvFileWriter.writerows(data)        
        bme280Ready = False

def mpu6050_consumer():
    global mpu6050Ready
    start = time.time()
    global mpu6050CsvFileWriter
    while running:
        mpu6050_condition.acquire()
        while not mpu6050Ready:
            mpu6050_condition.wait()
        mpu6050_condition.release()
        bus3.write_byte_data(MPU6050_ADDR, PWR_MGMT_1, 0)
        mpu6050_data = bus3.read_i2c_block_data(MPU6050_ADDR, ACCEL_XOUT_H, 14)
        end = time.time()
        current_total_time = end-start
        data = [
            [
                current_total_time ,
                start              ,
                end                ,
                mpu6050_data[0]    ,
                mpu6050_data[1]    ,
                mpu6050_data[2]    ,
                mpu6050_data[3]    ,
                mpu6050_data[4]    ,
                mpu6050_data[5]    ,
                mpu6050_data[6]    ,
                mpu6050_data[7]    ,
                mpu6050_data[8]    ,
                mpu6050_data[9]    ,
                mpu6050_data[10]   ,
                mpu6050_data[11]   ,
                mpu6050_data[12]   ,
                mpu6050_data[13]
            ]
        ]
        mpu6050CsvFileWriter.writerows(data)
        mpu6050Ready = False

def icm20948_consumer():
    global icm20948Ready
    global imu
    start = time.time()
    global icm20948CsvFileWriter
    while running:
        icm20948_condition.acquire()
        while not icm20948Ready:
            icm20948_condition.wait()
        icm20948_condition.release()
        if imu.dataReady():
            imu.getAgmt()
            ax = imu.axRaw
            ay = imu.ayRaw
            az = imu.azRaw
            gx = imu.gxRaw
            gy = imu.gyRaw
            gz = imu.gzRaw
            mx = imu.mxRaw
            my = imu.myRaw
            mz = imu.mzRaw
            temp = imu.tmpRaw
        end = time.time()
        current_total_time = end-start
        data = [
            [
                current_total_time ,
                start              ,
                end                ,
                ax                 ,
                ay                 ,
                az                 ,
                gx                 ,
                gy                 ,
                gz                 ,
                mx                 ,
                my                 ,
                mz                 ,
                temp
            ]
        ]
        icm20948CsvFileWriter.writerows(data)
        icm20948Ready = False

def on_frame(request):

    global frame_count
    global bme280Ready
    global mpu6050Ready
    global imx219Ready
    global icm20948Ready

    imx219_condition   .acquire()
    bme280_condition   .acquire()
    mpu6050_condition  .acquire()
    icm20948_condition .acquire()

    mpu6050_condition  .notify()
    imx219_condition   .notify()
    icm20948_condition .notify()

    imx219Ready   = True
    bme280Ready   = True
    mpu6050Ready  = True
    icm20948Ready = True

    if ((frame_count % 30) == 0):
        bme280_condition.notify()

    bme280_condition   .release()
    mpu6050_condition  .release()
    icm20948_condition .release()
    imx219_condition   .release()
    
    frame_count += 1
    frame_ready.set()


picam2  = Picamera2()
encoder = H264Encoder(bitrate=8000000)
config  = picam2.create_video_configuration(
    main     = {"format": "YUV420", "size": (1920, 1080)},
    controls = {"FrameDurationLimits": (33333, 33333)}  # 30fps = 1/30s = 33333μs
)
picam2.configure(config)
picam2.post_callback = on_frame

picam2.start()
picam2.start_encoder(encoder, output="output_h264encoder.h264")

print("Recording... Press Ctrl+C to stop.")

try:
    bme280_consumer_threading = threading.Thread(target=bme280_consumer)
    bme280_consumer_threading.start()

    mpu6050_consumer_threading = threading.Thread(target=mpu6050_consumer)
    mpu6050_consumer_threading.start()

    imx219_consumer_threading = threading.Thread(target=imx219_consumer)
    imx219_consumer_threading.start()

    icm20948_consumer_threading = threading.Thread(target=icm20948_consumer)
    icm20948_consumer_threading.start()

    start_unix_epoc = time.time()
    while running:
        if frame_ready.wait(timeout=1.0):
            frame_ready.clear()
            print(f"VSYNC Frame {frame_count} captured. " + str(frame_count%30) + " " + str(time.time() - start_unix_epoc) )
            
        else:
            print("Waiting for frame...")

    bme280_consumer_threading.join()
    mpu6050_consumer_threading.join()
    imx219_consumer_threading.join()
    icm20948_consumer_threading.join()
finally:
    picam2.stop_encoder()
    picam2.stop()
    print(f"Recording stopped. Total frames: {frame_count}")
    print("If you want to convert to MP4, please execute the following command.")
    print("ffmpeg -framerate 30 -i output_h264encoder.h264 -c copy output_h264encoder.mp4")
