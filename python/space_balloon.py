#!/usr/bin/env python
import math
import smbus2
import bme280
import FaBo9Axis_MPU9250
import qwiic_icm20948
import serial
import pynmea2
import subprocess
import time
import csv
import signal
import sys
import argparse
import threading
import multiprocessing
import shutil
import pandas
import matplotlib
import os
import re
import numpy
import datetime
import glob
import cv2
import openpyxl
from openpyxl.styles import PatternFill , Alignment , Font , Border , Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.table import Table, TableStyleInfo

########################################################################
class SensorWrapper:

    bme280_startedFlg   = False
    mpu6050_startedFlg  = False
    mpu9250_startedFlg  = False
    icm20948_startedFlg = False
    gps_startedFlg      = False

    def __init__( self , argv ):
        print("[Info] Create an instance of the SensorWrapper class.")
        self.argv                 = argv
        self.__bme280_fa          = None
        self.__mpu6050_fa         = None
        self.__mpu9250_fa         = None
        self.__icm20948_fa        = None
        self.__gps_fa             = None
        self.__bus                = None
        self.__mode               = None
        self.__output_dir         = None
        self.__camera_en          = None
        self.__gps_en             = None
        self.__bme280_en          = None
        self.__mpu6050_en         = None
        self.__mpu9250_en         = None
        self.__icm20948_en        = None
        self.__framerate          = None
        self.__bitrate            = None
        self.__width              = None
        self.__height             = None
        self.__gps_port           = None
        self.__bme280_addr        = None
        self.__mpu6050_addr       = None
        self.__icm20948_addr      = None
        self.__gps_csv            = None
        self.__bme280_csv         = None
        self.__mpu6050_csv        = None
        self.__mpu9250_csv        = None
        self.__icm20948_csv       = None
        self.__mp4_en             = None
        self.__altitude_en        = None
        self.__bme280_graph       = None
        self.__mpu6050_graph      = None
        self.__mpu9250_graph      = None
        self.__icm20948_graph     = None
        self.__tolerance          = None
        self.__tolerance_gps      = None
        self.__excel_en           = None

    def __handler( self , signum , frame ):
        self.__bme280_fa  .close()
        self.__mpu6050_fa .close()
        self.__mpu9250_fa .close()
        self.__icm20948_fa.close()
        self.__gps_fa     .close()
        self.__bus        .close()
        shutil.rmtree( './tmp' , ignore_errors=True )
        #sys.exit(0)

    def __read_args( self ):
        parser = argparse.ArgumentParser( description='option' , formatter_class=argparse.RawTextHelpFormatter )
        parser.add_argument( '--mode'       , '-m' , default=0     , required=True       , help="" )
        parser.add_argument( '--output_dir' , '-o' , default="./"                        , help="" )
        parser.add_argument( '--camera'            , default=False , action='store_true' , help="" )
        parser.add_argument( '--gps'               , default=False , action='store_true' , help="" )
        parser.add_argument( '--bme280'            , default=False , action='store_true' , help="" )
        parser.add_argument( '--mpu6050'           , default=False , action='store_true' , help="" )
        parser.add_argument( '--mpu9250'           , default=False , action='store_true' , help="" )
        parser.add_argument( '--icm20948'          , default=False , action='store_true' , help="" )
        parser.add_argument( '--framerate'         , default="30"                        , help="" )
        parser.add_argument( '--bitrate'           , default="8000000"                   , help="" )
        parser.add_argument( '--width'             , default="1920"                      , help="" )
        parser.add_argument( '--height'            , default="1080"                      , help="" )
        parser.add_argument( '--gps_port'          , default="/dev/ttyACM0"              , help="" )
        parser.add_argument( '--bme280_addr'       , default="0x76"                      , help="" )
        parser.add_argument( '--mpu6050_addr'      , default="0x68"                      , help="" )
        parser.add_argument( '--icm20948_addr'     , default="0x68"                      , help="" )
        parser.add_argument( '--frame_sync'        , default=False , action='store_true' , help="" )
        parser.add_argument( '--movie_csv'                                               , help="" )
        parser.add_argument( '--gps_csv'                                                 , help="" )
        parser.add_argument( '--bme280_csv'                                              , help="" )
        parser.add_argument( '--mpu6050_csv'                                             , help="" )
        parser.add_argument( '--mpu9250_csv'                                             , help="" )
        parser.add_argument( '--icm20948_csv'                                            , help="" )
        parser.add_argument( '--mp4'               , default=False , action='store_true' , help="" )
        parser.add_argument( '--altitude'          , default=False , action='store_true' , help="" )
        parser.add_argument( '--bme280_graph'      , default=False , action='store_true' , help="" )
        parser.add_argument( '--mpu6050_graph'     , default=False , action='store_true' , help="" )
        parser.add_argument( '--mpu9250_graph'     , default=False , action='store_true' , help="" )
        parser.add_argument( '--icm20948_graph'    , default=False , action='store_true' , help="" )
        parser.add_argument( '--movie'                                                   , help="" )
        parser.add_argument( '--tolerance'         , default=0.032                       , help="" )
        parser.add_argument( '--tolerance_gps'     , default=1                           , help="" )
        parser.add_argument( '--excel'             , default=False , action='store_true' , help="" )
        try:
            args                     = parser.parse_args()
            self.__mode              = int( args.mode )
            self.__output_dir        = args.output_dir
            self.__camera_en         = int( args.camera  )
            self.__gps_en            = int( args.gps  )
            self.__bme280_en         = int( args.bme280  )
            self.__mpu6050_en        = int( args.mpu6050 )
            self.__mpu9250_en        = int( args.mpu9250 )
            self.__icm20948_en       = int( args.icm20948 )
            self.__framerate         = int( args.framerate )
            self.__bitrate           = int( args.bitrate )
            self.__width             = int( args.width )
            self.__height            = int( args.height )
            self.__gps_port          = args.gps_port
            self.__bme280_addr       = int( args.bme280_addr   , 16 )
            self.__mpu6050_addr      = int( args.mpu6050_addr  , 16 )
            self.__icm20948_addr     = int( args.icm20948_addr , 16 )
            self.__movie_csv         = args.movie_csv
            self.__gps_csv           = args.gps_csv
            self.__bme280_csv        = args.bme280_csv
            self.__mpu6050_csv       = args.mpu6050_csv
            self.__mpu9250_csv       = args.mpu9250_csv
            self.__icm20948_csv      = args.icm20948_csv
            self.__frame_sync_en     = int( args.frame_sync )
            self.__mp4_en            = int( args.mp4 )
            self.__altitude_en       = int( args.altitude )
            self.__bme280_graph_en   = int( args.bme280_graph )
            self.__mpu6050_graph_en  = int( args.mpu6050_graph )
            self.__mpu9250_graph_en  = int( args.mpu9250_graph )
            self.__icm20948_graph_en = int( args.icm20948_graph )
            self.__movieFile         = args.movie
            self.__tolerance         = float(args.tolerance)
            self.__tolerance_gps     = float(args.tolerance_gps)
            self.__excel_en          = int( args.excel )

        except Exception as e:
            print(e)
            sys.exit(1)

    def __setup_sensors( self ):
        print("[Info] Start the __generate_empty_csvFile function.")

        csvUnixEpochTimeStr = str( time.time() )
        bme280CsvFile       = self.__output_dir + "/bme280_"   + csvUnixEpochTimeStr + ".csv"
        mpu6050CsvFile      = self.__output_dir + "/mpu6050_"  + csvUnixEpochTimeStr + ".csv"
        mpu9250CsvFile      = self.__output_dir + "/mpu9250_"  + csvUnixEpochTimeStr + ".csv"
        icm20948CsvFile     = self.__output_dir + "/icm20948_" + csvUnixEpochTimeStr + ".csv"
        gpsCsvFile          = self.__output_dir + "/gps_"      + csvUnixEpochTimeStr + ".csv"
        self.__bus          = smbus2.SMBus(1)

        if self.__camera_en :
            print("[Info] Activate the Camera Module.")
            self.__cameraModuleImpl = CameraModuleImpl(
                self.__output_dir ,
                self.__framerate  ,
                self.__bitrate    ,
                self.__width      ,
                self.__height
            )
            
        if self.__gps_en :
            print("[Info] Activate the IVK172 G-Mouse USB GPS.")
            data = [
                [
                    'elapsed_time'       ,
                    'start_epoch_time'   ,
                    'unix_epoch_time'    
                    'latitude'           ,
                    'longitude'          ,
                    'altitude'           
                    'num_sats'           ,
                    # 'datestam'           ,
                    # 'timestamp'          ,
                    'spd_over_grnd'      ,
                    'true_course'        ,
                    'true_track'         ,
                    'spd_over_grnd_kmph' ,
                    'pdop'               ,
                    'hdop'               ,
                    'vdop'               ,
                    'num_sv_in_view'
                ]
            ]
            # self.__generate_empty_csvFile( gpsCsvFile , data )
            # self.__gps_fa , gps_fw = self.__get_csvFile( gpsCsvFile )
            # self.__gpsModuleImpl   = GPSModuleImpl( self.__gps_port , gps_fw )
            self.__generate_empty_csvFile( "output/gps_data.csv" , data )
            self.__gps_fa , gps_fw = self.__get_csvFile( "output/gps_data.csv" )
            self.__gpsModuleImpl   = GPSModuleImpl( self.__gps_port , gps_fw )

        if self.__icm20948_en :
            print("[Info] Activate the ICM-20948.")
            data = [
                [
                    'elapsed_time'     ,
                    'start_epoch_time' ,
                    'unix_epoch_time'  ,
                    'ax'               ,
                    'ay'               ,
                    'az'               ,
                    'gx'               ,
                    'gy'               ,
                    'gz'               ,
                    'mx'               ,
                    'my'               ,
                    'mz'               ,
                    'temperature'
                ]
            ]
            self.__generate_empty_csvFile( icm20948CsvFile , data )
            self.__icm20948_fa , icm20948_fw = self.__get_csvFile( icm20948CsvFile )
            self.__icm20948Impl = ICM20948Impl( self.__icm20948_addr , icm20948_fw )

        if self.__bme280_en :
            print("[Info] Activate the BME280.")
            data = [
                [
                    'elapsed_time'     ,
                    'start_epoch_time' ,
                    'unix_epoch_time'  ,
                    'temperature'      ,
                    'pressure'         ,
                    'humidity'
                ]
            ]
            self.__generate_empty_csvFile( bme280CsvFile , data )
            self.__bme280_fa , bme280_fw = self.__get_csvFile( bme280CsvFile )
            self.__bme280Impl            = BME280Impl  ( self.__bus , self.__bme280_addr , bme280_fw  )
        else:
             SensorWrapper.bme280_startedFlg = True

        if self.__mpu6050_en:
            print("[Info] Activate the MPU6050.")
            data = [
                [
                    'elapsed time'     ,
                    'start_epoch_time' ,
                    'unix_epoch_time'  ,
                    'ax'               ,
                    'ay'               ,
                    'az'               ,
                    'gx'               ,
                    'gy'               ,
                    'gz'               ,
                    'temperature'
                ]
            ]
            self.__generate_empty_csvFile( mpu6050CsvFile ,data )
            self.__mpu6050_fa , mpu6050_fw = self.__get_csvFile( mpu6050CsvFile )
            self.__mpu6050Impl             = MPU6050Impl( self.__bus , self.__mpu6050_addr , mpu6050_fw )
        else:
            SensorWrapper.mpu6050_startedFlg = True

        if self.__mpu9250_en:
            print("[Info] Activate the MPU9250.")
            data = [
                [
                    'elapsed_time'     ,
                    'start_epoch_time' ,
                    'unix_epoch_time'  ,
                    'accel'            ,
                    'gyro'             ,
                    'magnet'
                ]
            ]
            self.__generate_empty_csvFile( mpu9250CsvFile , data )
            self.__mpu9250_fa , mpu9250_fw = self.__get_csvFile( mpu9250CsvFile )
            self.__mpu9250Impl             = MPU9250Impl( mpu9250_fw )
        else:
            SensorWrapper.mpu9250_startedFlg = True

    def __generate_empty_csvFile( self , csvFileName , data ):
        print("[Info] Create the  " + csvFileName + ".")
        fopen  = open( csvFileName , 'w' , newline='' , encoding='utf-8' )
        writer = csv.writer( fopen )
        writer.writerows( data )
        fopen.close()

    def __get_csvFile( self , csvFileName ):
        fappend = open( csvFileName , 'a' , newline='' , encoding='utf-8' )
        writer  = csv.writer( fappend )
        return fappend , writer

    def __garbage_colloction( self ):
        pass

    def doSensorWrapper(self):
        print("[Info] Start the doSensorWrapper function.")
        self.__read_args()

        if self.__mode == 0:
            print("[Info] It operates in sensor data output mode.")
            self.__setup_sensors()
            threadList = []
            signal.signal( signal.SIGINT , self.__handler )
            try:
                if self.__bme280_en:
                    bme280Thread   = threading.Thread( target=self.__bme280Impl.doBME280Impl)
                    threadList.append(bme280Thread)
                if self.__mpu6050_en:
                    mpu6050Thread  = threading.Thread( target=self.__mpu6050Impl.doMPU6050Impl )
                    threadList.append(mpu6050Thread)
                if self.__mpu9250_en:
                    mpu9250Thread  = threading.Thread( target=self.__mpu9250Impl.doMPU9250Impl )
                    threadList.append(mpu9250Thread)
                if self.__camera_en :
                    cameraThread   = threading.Thread( target=self.__cameraModuleImpl.doCameraModuleImpl )
                    threadList.append(cameraThread)
                if self.__gps_en    :
                    gpsThread      =  threading.Thread( target=self.__gpsModuleImpl.doGpsModuleImpl )
                    threadList.append(gpsThread)
                if self.__icm20948_en    :
                    icm20948Thread =  threading.Thread( target=self.__icm20948Impl.doIcm20948Impl )
                    threadList.append(icm20948Thread)
                for singleThread in threadList:
                    singleThread.start()
                self.__garbage_colloction() # GC
                for singleThread in threadList:
                    singleThread.join()
            except Exception as e:
                print(e)

        elif self.__mode == 1:
            print("[Info] It operates in sensor data reading and analysis mode.")
            sai = SensorAnalyzerImpl(
                self.__movieFile        ,
                self.__mp4_en           ,
                self.__altitude_en      ,
                self.__bme280_graph_en  ,
                self.__mpu6050_graph_en ,
                self.__mpu9250_graph_en ,
                self.__icm20948_graph   ,
                self.__frame_sync_en    ,
                self.__gps_csv          ,
                self.__bme280_csv       ,
                self.__mpu6050_csv      ,
                self.__mpu9250_csv      ,
                self.__icm20948_csv     ,
                self.__movie_csv        ,
                self.__tolerance        ,
                self.__tolerance_gps    ,
                self.__excel_en
            )
            sai.doSensorAnalyzerImplImpl()

########################################################################
class CameraModuleImpl:

    def __init__( self , csvFilePath , framerate , bitrate , width , height ):
        print("[Info] Create an instance of the CameraModuleImpl class.")
        self.__csvFilePath = csvFilePath
        self.__framerate   = framerate
        self.__bitrate     = bitrate
        self.__width       = width
        self.__height      = height

    def __start_camera_module( self ):
        while True:
            if  SensorWrapper.mpu9250_startedFlg and  SensorWrapper.mpu9250_startedFlg and  SensorWrapper.mpu9250_startedFlg and SensorWrapper.icm20948_startedFlg and SensorWrapper.gps_startedFlg:
                break
            else:
                time.sleep(1)

        subprocess.run(
            "libcamera-vid --framerate "    + str( self.__framerate) +
            " --bitrate "                   + str( self.__bitrate ) +
            " --width "                     + str( self.__width ) +
            " --height "                    + str( self.__height ) +
            " --save-pts "                  + str( self.__csvFilePath ) + "/video_"
            + str(time.time()) + ".csv -o " + str( self.__csvFilePath ) +"/video_"
            + str(time.time()) +".h264 --timeout 0 --nopreview",
            shell          = True ,
            capture_output = True ,
            text           = True
        )

    def doCameraModuleImpl( self ):
        print("[Info] Start the doCameraModuleImpl function.")
        try:
            self.__start_camera_module()
        except Exception as e:
            print(e)

########################################################################
class GPSModuleImpl:

    def __init__( self , port  , csvFile ):
        print("[Info] Create an instance of the GPSModuleImpl class.")
        print("[Info] The port for the IVK172 G-Mouse USB GPS is " + str(port) + ".")
        self.__start_unix_epoch_time = 0
        self.__latitude              = None
        self.__longitude             = None
        self.__altitude              = None
        self.__altitude_units        = None
        self.__num_sats              = None
        self.__datestamp             = None
        self.__timestamp             = None
        self.__spd_over_grnd         = None
        self.__true_course           = None
        self.__true_track            = None
        self.__spd_over_grnd_kmph    = None
        self.__pdop                  = None
        self.__hdop                  = None
        self.__vdop                  = None
        self.__num_sv_in_view        = None
        self.__csvFile               = csvFile
        self.__ser                   = serial.Serial( port , 9600 , timeout=1 )
        
    def __read_sensor( self ):
        frame = {"GGA": None, "RMC": None, "VTG": None, "GSA": None, "GSV": None}
        try:
            while True:
            
                raw = self.__ser.readline().decode('ascii', errors='replace').strip()
                if not raw.startswith('$'):
                    continue

                msg = None
                try:
                    rawmsg = pynmea2.parse(raw)
                    msg = rawmsg
                except pynmea2.ParseError:
                    pass
                    
                if msg is None:
                    continue

                key = msg.sentence_type
                if key in frame:
                    frame[key] = msg
                if all(frame.values()):
                    gga , rmc , vtg , gsa , gsv = ( frame["GGA"] , frame["RMC"] , frame["VTG"] , frame["GSA"] , frame["GSV"] )
                    self.__latitude           = gga.latitude
                    self.__longitude          = gga.longitude
                    self.__altitude           = gga.altitude
                    self.__altitude_units     = gga.altitude_units
                    self.__num_sats           = gga.num_sats
                    self.__datestamp          = rmc.datestamp
                    self.__timestamp          = rmc.timestamp
                    self.__spd_over_grnd      = rmc.spd_over_grnd
                    self.__true_course        = rmc.true_course
                    self.__true_track         = vtg.true_track
                    self.__spd_over_grnd_kmph = vtg.spd_over_grnd_kmph
                    self.__pdop               = gsa.pdop
                    self.__hdop               = gsa.hdop
                    self.__vdo                = gsa.vdop
                    self.__num_sv_in_view     = gsv.num_sv_in_view
                    frame = dict.fromkeys(frame, None)
                        
        except KeyboardInterrupt as e:
            pass # ignore
        finally:
            self.__ser.close()
   
    def __output_csv(self):
        while True:
            try:
                end_unix_epoch_time = time.time()
                total_time = end_unix_epoch_time - self.__start_unix_epoch_time

                if (self.__latitude is not None) and (self.__longitude is not None) and (self.__altitude is not None):

                    data = [
                        [
                            total_time                   ,
                            self.__start_unix_epoch_time ,
                            end_unix_epoch_time          
                            self.__latitude              ,
                            self.__longitude             ,
                            self.__altitude              ,
                            self.__altitude_units        ,
                            self.__num_sats              ,
                            # self.__datestamp             ,
                            # self.__timestamp             ,
                            self.__spd_over_grnd         ,
                            self.__true_course           ,
                            self.__true_track            ,
                            self.__spd_over_grnd_kmph    ,
                            self.__pdop                  ,
                            self.__hdop                  ,
                            self.__vdo                   ,
                            self.__num_sv_in_view     
                        ]
                    ]
                    self.__csvFile.writerows( data )
                    self.__latitude           = None
                    self.__longitude          = None
                    self.__altitude           = None
                    self.__altitude_units     = None
                    self.__num_sats           = None
                    self.__datestamp          = None
                    self.__timestamp          = None
                    self.__spd_over_grnd      = None
                    self.__true_course        = None
                    self.__true_track         = None
                    self.__spd_over_grnd_kmph = None
                    self.__pdop               = None
                    self.__hdop               = None
                    self.__vdo                = None
                    self.__num_sv_in_view     = None
                    if SensorWrapper.gps_startedFlg is False:
                        print("[Info] IVK172 G-Mouse USB GPS Started.")
                        SensorWrapper.gps_startedFlg = True
                #time.sleep(0.0005)
            except Exception as e:
                print(e)
                
    def doGpsModuleImpl(self):
        print("[Info] Start the doGpsModuleImpl function.")
        try:
            self.__start_unix_epoch_time = time.time()
            outputThread                 = threading.Thread( target=self.__output_csv )
            outputThread.start()
            self.__read_sensor()
        except Exception as e:
            pass # ignore

########################################################################
class BME280Impl:

    def __init__( self , bus , address , csvFile ):
        print("[Info] Create an instance of the BME280Impl class.")
        print("[Info] The device address of the BME280 is " + str(hex(address)) )
        self.__start_unix_epoch_time = 0
        self.__temperature = None
        self.__pressure    = None
        self.__humidity    = None
        self.__csvFile     = csvFile
        # --- I2C設定 ---
        self.__address     = address
        self.__bus         = bus
        # --- BME/BMP280の初期化 ---
        self.__calibration_params = bme280.load_calibration_params( self.__bus , self.__address )

    def __read_sensor(self):
        data               = bme280.sample( self.__bus , self.__address , self.__calibration_params )
        self.__temperature = data.temperature # [°]
        self.__pressure    = data.pressure    # [hPa]
        self.__humidity    = data.humidity    # [%]

    def __output_csv(self):
        while True:
            end_unix_epoch_time = time.time()
            total_time = end_unix_epoch_time - self.__start_unix_epoch_time
            if self.__temperature and self.__pressure and self.__humidity:
                data = [
                    [
                        total_time                   ,
                        self.__start_unix_epoch_time ,
                        end_unix_epoch_time          ,
                        self.__temperature           ,
                        self.__pressure              ,
                        self.__humidity
                    ]
                ]
                self.__csvFile.writerows( data )
                self.__temperature = None
                self.__pressure    = None
                self.__humidity    = None
                if SensorWrapper.bme280_startedFlg is False:
                    print("[Info] BME280 Started.")
                    SensorWrapper.bme280_startedFlg = True
            time.sleep(0.0005)

    def doBME280Impl(self):
        print("[Info] Start the doBME280Impl function.")
        try:
            self.__start_unix_epoch_time = time.time()
            outputThread = threading.Thread( target=self.__output_csv )
            outputThread.start()
            while True:
                self.__read_sensor()
                time.sleep(0.001)
        except Exception as e:
            print(e)

########################################################################
class MPU6050Impl:

    def __init__( self , bus , address , csvFile ):
        print("[Info] Create an instance of the MPU6050Impl class.")
        print("[Info] The device address of the MPU6050 is " + str(hex(address)) )
        self.__start_unix_epoch_time = 0
        self.__ax                    = None
        self.__ay                    = None
        self.__az                    = None
        self.__gx                    = None
        self.__gy                    = None
        self.__gz                    = None
        self.__temperature           = None
        self.__csvFile               = csvFile
        # --- I2C設定 ---
        self.__address               = address
        self.__bus                   = bus

    def __read_word( self , addr ):
        high = self.__bus.read_byte_data( self.__address , addr   )
        low  = self.__bus.read_byte_data( self.__address , addr+1 )
        val = (high << 8) + low
        if( val < 0x8000 ):
            return val
        else:
            return val - 65536

    def __read_sensor( self ):
        PWR_MGMT_1a  = 0x6B
        ACCEL_XOUT_H = 0x3B
        ACCEL_YOUT_H = 0x3D
        ACCEL_ZOUT_H = 0x3F
        GYRO_XOUT_H  = 0x43
        GYRO_YOUT_H  = 0x45
        GYRO_ZOUT_H  = 0x47
        TEMP_OUT_H   = 0x41
        self.__bus.write_byte_data( self.__address , PWR_MGMT_1a , 0 )
        self.__ax          =   self.__read_word( ACCEL_XOUT_H ) / 16384.0
        self.__ay          =   self.__read_word( ACCEL_YOUT_H ) / 16384.0
        self.__az          =   self.__read_word( ACCEL_ZOUT_H ) / 16384.0
        self.__gx          =   self.__read_word( GYRO_XOUT_H  ) / 131.0
        self.__gy          =   self.__read_word( GYRO_YOUT_H  ) / 131.0
        self.__gz          =   self.__read_word( GYRO_ZOUT_H  ) / 131.0
        self.__temperature = ( self.__read_word( TEMP_OUT_H ) + 521 ) / 340.0 + 35.0

    def __output_csv(self):
        while True:
            end_unix_epoch_time = time.time()
            total_time = end_unix_epoch_time - self.__start_unix_epoch_time
            if self.__ax and self.__ay and self.__az and self.__gx and self.__gy and self.__gz and self.__temperature:
                data = [
                    [
                        total_time                   ,
                        self.__start_unix_epoch_time ,
                        end_unix_epoch_time          ,
                        self.__ax                    ,
                        self.__ay                    ,
                        self.__az                    ,
                        self.__gx                    ,
                        self.__gy                    ,
                        self.__gz                    ,
                        self.__temperature
                    ]
                ]
                self.__csvFile.writerows( data )
                self.__ax          = None
                self.__ay          = None
                self.__az          = None
                self.__gx          = None
                self.__gy          = None
                self.__gz          = None
                self.__temperature = None
                if SensorWrapper.mpu6050_startedFlg is False:
                    print("[Info] MPU6050 Started.")
                    SensorWrapper.mpu6050_startedFlg = True
            time.sleep(0.0005)

    def doMPU6050Impl(self):
        print("[Info] Start the doMPU6050Impl function.")
        try:
            self.__start_unix_epoch_time = time.time()
            outputThread                 = threading.Thread( target=self.__output_csv )
            outputThread.start()
            while True:
                self.__read_sensor()
                #time.sleep(0.001) # 1msec
        except Exception as e:
            print(e)

########################################################################
class MPU9250Impl:

    def __init__( self , csvFile ):
        print("[Info] Create an instance of the MPU9250Impl class.")
        self.__start_unix_epoch_time = 0
        self.__accel                 = None
        self.__gyro                  = None
        self.__magnet                = None
        self.__csvFile               = csvFile

    def __read_sensor( self ):
        mpu9250 = FaBo9Axis_MPU9250.MPU9250()
        self.__accel  = mpu9250.readAccel()
        self.__gyro   = mpu9250.readGyro()
        self.__magnet = mpu9250.readMagnet()

    def __output_csv(self):
        while True:
            end_unix_epoch_time = time.time()
            total_time          = end_unix_epoch_time - self.__start_unix_epoch_time
            if self.__accel and self.__gyro and self.__magnet:
                data = [
                    [
                        total_time                   ,
                        self.__start_unix_epoch_time ,
                        end_unix_epoch_time          ,
                        self.__accel                 ,
                        self.__gyro                  ,
                        self.__magnet
                    ]
                ]
                self.__csvFile.writerows( data )
                self.__accel  = None
                self.__gyro   = None
                self.__magnet = None
                if SensorWrapper.mpu9250_startedFlg is False:
                    print("[Info] MPU9250 Started.")
                    SensorWrapper.mpu9250_startedFlg = True
            time.sleep(0.0005)

    def doMPU9250Impl(self):
        print("[Info] Start the doMPU9520Impl function.")
        try:
            self.__start_unix_epoch_time = time.time()
            outputThread = threading.Thread( target=self.__output_csv )
            outputThread.start()
            while True:
                self.__read_sensor()
                #time.sleep(0.001) # 1msec
        except Exception as e:
            print(e)

########################################################################
class ICM20948Impl:

    def __init__( self , address , csvFile ):
        print("[Info] Create an instance of the ICM20948Impl class.")
        print("[Info] The device address of the ICM-20948 is " + str(hex(address)) )
        self.__start_unix_epoch_time = 0
        self.__ax                    = None
        self.__ay                    = None
        self.__az                    = None
        self.__gx                    = None
        self.__gy                    = None
        self.__gz                    = None
        self.__mx                    = None
        self.__my                    = None
        self.__mz                    = None
        self.__temperature           = None
        self.__csvFile               = csvFile
        # --- I2C設定 ---
        self.__imu                   = qwiic_icm20948.QwiicIcm20948( address )

    def __read_sensor( self ):
        if self.__imu.dataReady():
            self.__imu.getAgmt()
            self.__ax          = self.__imu.axRaw
            self.__ay          = self.__imu.ayRaw
            self.__az          = self.__imu.azRaw
            self.__gx          = self.__imu.gxRaw
            self.__gy          = self.__imu.gyRaw
            self.__gz          = self.__imu.gzRaw
            self.__mx          = self.__imu.mxRaw
            self.__my          = self.__imu.myRaw
            self.__mz          = self.__imu.mxRaw
            self.__temperature = (self.__imu.tmpRaw/333.87)+21

    def __output_csv(self):
        while True:
            end_unix_epoch_time = time.time()
            total_time = end_unix_epoch_time - self.__start_unix_epoch_time
            if (self.__ax is not None) and (self.__ay is not None) and (self.__az is not None) and (self.__gx is not None) and (self.__gy is not None) and (self.__gz is not None) and (self.__mx is not None) and (self.__my is not None) and (self.__mz is not None) and (self.__temperature is not None):
                data = [
                    [
                        total_time                   ,
                        self.__start_unix_epoch_time ,
                        end_unix_epoch_time          ,
                        self.__ax                    ,
                        self.__ay                    ,
                        self.__az                    ,
                        self.__gx                    ,
                        self.__gy                    ,
                        self.__gz                    ,
                        self.__mx                    ,
                        self.__my                    ,
                        self.__mz                    ,
                        self.__temperature
                    ]
                ]
                self.__csvFile.writerows( data )
                self.__ax          = None
                self.__ay          = None
                self.__az          = None
                self.__gx          = None
                self.__gy          = None
                self.__gz          = None
                self.__mx          = None
                self.__my          = None
                self.__mz          = None
                self.__temperature = None
                if SensorWrapper.icm20948_startedFlg is False:
                    print("[Info] ICM-20948 Started.")
                    SensorWrapper.icm20948_startedFlg = True
            time.sleep(0.0005)

    def doIcm20948Impl(self):
        print("[Info] Start the doIcm20948Impl function.")
        try:
            self.__start_unix_epoch_time = time.time()
            outputThread                 = threading.Thread( target=self.__output_csv )
            outputThread.start()
            while True:
                self.__read_sensor()
                #time.sleep(0.001) # 1msec
        except Exception as e:
            print(e)

########################################################################
class SensorAnalyzerImpl:

    def __init__(
            self             ,
            movieFile        ,
            mp4_en           ,
            altitude_en      ,
            bme280_graph_en  ,
            mpu6050_graph_en ,
            mpu9250_graph_en ,
            icm20948_graph   ,
            frame_sync_en    ,
            bme280_csv       ,
            mpu6050_csv      ,
            mpu9250_csv      ,
            icm20948_csv     ,
            movie_csv        ,
            tolerance        ,
            tolerance_gps    ,
            excel_en
    ):
        print("[Info] Create an instance of the SensorAnalyzerImpl class.")
        self.__movieFile        = movieFile
        self.__mp4_en           = mp4_en
        self.__altitude_en      = altitude_en
        self.__bme280_graph_en  = bme280_graph_en
        self.__mpu6050_graph_en = mpu6050_graph_en
        self.__mpu9250_graph_en = mpu9250_graph_en
        self.__icm20948_graph   = icm20948_graph
        self.__frame_sync_en    = frame_sync_en
        self.__gps_csv          = gps_csv
        self.__bme280_csv       = bme280_csv
        self.__mpu6050_csv      = mpu6050_csv
        self.__mpu9250_csv      = mpu9250_csv
        self.__icm20948_csv     = icm20948_csv
        self.__movie_csv        = movie_csv
        self.__tolerance        = tolerance
        self.__tolerance_gps    = tolerance_gps
        self.__excel_en         = excel_en

    def __convert_h264_to_mp4( self , movieFileName ):
        print("[Info] Start the __convert_h264_to_mp4 function.")
        if shutil.which("MP4Box") is not None:
            if movieFileName is not None:
                print("[Info] Convert from H.264 to MP4.")
                print("[Info] MP4Box -add " + movieFileName + " " + movieFileName + ".mp4")
                subprocess.run(
                    "MP4Box -add " + movieFileName + " " + movieFileName + ".mp4" ,
                    shell=True , capture_output=True , text=True
                )
            else:
                print("[Warn] Please set the video file name.")
        else:
            print("[Warn] Install it with the following command.")
            print("[Warn] apt install -y gpac")

    def __generate_map_html( self ):
        dataFrame     = pandas.read_csv( self.__gps_csv )
        folium_figure = folium.Figure(width=1500, height=700)
        center_lat    = 35
        center_lon    = 139
        folium_map    = folium.Map( [ center_lat , center_lon ] , zoom_start=4.5 ).add_to( folium_figure )
        for i in range( dataFrame.count()["latitude"] ):
            folium.Marker( location=[ dataFrame.loc[ i , "latitude" ] , dataFrame.loc[ i , "longitude" ] ] ).add_to( folium_map )
        folium_map.save( self.__gps_csv + ".html" )

    def __generate_map_kml( self ):
        dataFrame                        = pandas.read_csv( os.path.join(os.getcwd(),path) , header=0 )
        tuple_B                          =  [tuple(x) for x in df_B[['longitude','latitude','altitude']].values]
        kml                              = simplekml.Kml(open=1)
        linestring                       = kml.newlinestring(name="A Sloped Line")
        linestring.coords                = tuple_B
        linestring.altitudemode          = simplekml.AltitudeMode.relativetoground
        linestring.extrude               = 0
        linestring.style.linestyle.width = 3
        linestring.style.linestyle.color = simplekml.Color.red
        kml.save( self.__gps_csv + ".kml" )

    def __generate_alititude_csv( self ):
        print("[Info] Start the __generate_alititude_csv function.")
        dataFrame = pandas.read_csv( self.__bme280_csv )
        basename , extension = os.path.splitext( self.__bme280_csv )
        dataFrame['altitude'] = dataFrame.apply(
            lambda row :  self.__calculate_altitude(
                row['temperature'] , row['humidity'] , row['pressure'] ) , axis=1
        )
        dataFrame['current_time']     = dataFrame['unix_epoch_time'].apply(
            lambda epoch_time_ms :
            datetime.datetime.fromtimestamp(epoch_time_ms).strftime('%Y-%m-%d %H:%M:%S.') +
            f'{datetime.datetime.fromtimestamp(epoch_time_ms).microsecond // 1000:03d}'
        )
        cols = list( dataFrame.columns )
        cols.remove( 'current_time' )
        insert_pos = cols.index('unix_epoch_time') + 1
        cols.insert( insert_pos , 'current_time' )
        dataFrame = dataFrame[cols]

        if self.__excel_en:
            self.__output_to_excel( "bme280" , basename + "_altitude.xlsx" , dataFrame )
            #dataFrame.to_excel(  basename + "_altitude.xlsx" , index=False )
        else:
            dataFrame.to_csv  (  basename + "_altitude.csv"  , index=False )
        return dataFrame

    def __output_to_excel( self , sheetName , fileName , dataFrame ):
        wb              = openpyxl.Workbook()
        ws              = wb.active
        ws.title        = sheetName
        ws.freeze_panes = 'B2'
        font            = Font(name='BIZ UDゴシック', size=11)
        no_border = Border(
            # left   = Side( border_style=None ) ,
            # right  = Side( border_style=None ) ,
            # top    = Side( border_style=None ) ,
            # bottom = Side( border_style=None )
            left    = Side( style='thin' ) ,
            right   = Side( style='thin' ) ,
            top     = Side( style='thin' ) ,
            bottom  = Side( style='thin' )
        )

        # Data writing & font/border settings
        for r_idx, row in enumerate( dataframe_to_rows( dataFrame , index=False , header=True ) , start=1 ):
            for c_idx , value in enumerate( row , start=1 ):
                cell        = ws.cell(row=r_idx, column=c_idx, value=value)
                cell.font   = font
                cell.border = no_border
                if r_idx == 1:
                    cell.fill      = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
                    cell.alignment = Alignment( horizontal='center', vertical='center' )

        # Auto-adjust column width
        for col_idx, column_cells in enumerate( ws.columns , start=1 ):
            max_length     = max( len( str(cell.value) ) if cell.value is not None else 0 for cell in column_cells )
            adjusted_width = max_length + 2.5
            col_letter     = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = adjusted_width
        ws.auto_filter.ref = ws.dimensions
        wb.save( fileName )

    def __calculate_altitude( self , Tc , RH , P ):
        P0  = 1013.25     # 海面上の標準気圧[hPa]
        L   = 0.0065      # 温度減率[K/m]
        g   = 9.80665     # 重力加速度[m/s^2]
        R   = 8.314462618 # 気体定数[J/(mol·K)]
        M   = 0.0289644   # 空気のモル質量[kg/mol]
        Pu  = 226.32      # 標準大気における11kmの気圧[hPa]
        if RH is None or RH <= 0: # 湿度データが無い場合は実測温度を使う
            Tu = Tc + 273.15 # [K]
        else:                     # 湿度データがある場合は仮想温度を使う
            Tu = self.__virtual_temperature( Tc , RH , P )
        if P > Pu:                # 対流圏 (11km以下)
            h = (Tu / L) * (1 - (P / P0) ** ((R * L) / (g * M)))
        else:                     # 成層圏 (11km以上)
            h = 11000 + ( R * Tu ) / ( g * M ) * math.log( Pu / P )
        return h

    def __virtual_temperature( self , Tc , RH , P ):
        Tk  = Tc + 273.15  # 気温をKに変換
        es  = 6.112 * math.exp( (17.67*Tc) / (Tc+243.5) ) # 飽和水蒸気圧(Tetensの式)es[hPa]
        e   = (RH / 100.0) * es                           # 実際の水蒸気圧e[hPa]
        r   = ((0.622*e) / (P-e)) / 1000                  # 混合比r[kg/kg]
        Tkv = Tk * ( 1 + 0.61 * r )                       # 仮想温度[K]
        return Tkv

    def __generate_bme280_graph( self ):
        print("[Info] Start the __generate_bme280_graph function.")

    def __generate_mpu6050_graph( self ):
        print("[Info] Start the __generate_mpu6050_graph function.")

    def __generate_mpu9250_graph( self ):
        print("[Info] Start the __generate_mpu9250_graph function.")

    def __generate_mpu6050_graph( self ):
        print("[Info] Start the __generate_mpu6050_graph function.")

    def __analyse_frame_sync( self , bme280DataFrame ):
        print("[Info] Start the __analyse_frame_sync function.")
        if self.__movie_csv is not None:
            dataFrame                     = pandas.read_csv( self.__movie_csv )
            dataFrame.columns             = ['milli_sec_elapsed_time'] 
            basename , extension          = os.path.splitext( self.__movie_csv )
            dataFrame['sec_elapsed_time'] = dataFrame['milli_sec_elapsed_time'] / 1000

            if self.__movieFile is not None:
                movie_start_time = float(
                    str(re.sub(r"^.*_", "", self.__movieFile )).replace(".h264","")
                ) # unix epoch time
                dataFrame['unix_epoch_time']  = movie_start_time + dataFrame['sec_elapsed_time']
            
                dataFrame['current_time']     = dataFrame['unix_epoch_time'].apply(
                    lambda epoch_time_ms :
                    datetime.datetime.fromtimestamp(epoch_time_ms).strftime('%Y-%m-%d %H:%M:%S.') +
                    f'{datetime.datetime.fromtimestamp(epoch_time_ms).microsecond // 1000:03d}'
                )

                if self.__bme280_csv  is not None:
                    matchTolerance  = []

                    if bme280DataFrame is None:
                        bme280DataFrame = pandas.read_csv( self.__bme280_csv )
                    else:
                        bme280DataFrame = bme280DataFrame.drop(columns=['current_time'])

                    for unix_epoch_time in dataFrame['unix_epoch_time']:
                        match = bme280DataFrame[
                            ( bme280DataFrame['unix_epoch_time'] >= unix_epoch_time - self.__tolerance ) &
                            ( bme280DataFrame['unix_epoch_time'] <= unix_epoch_time + self.__tolerance )
                        ].copy()
    
                        if not match.empty:
                            match['bme280_unix_epoch_time_delta'] = abs(match['unix_epoch_time'] - unix_epoch_time)
                            match                                 = match.loc[match['bme280_unix_epoch_time_delta'].idxmin()]
                            match                                 = match.to_frame().T
                            if self.__altitude_en:
                                match_row                             = match.rename(
                                    columns={
                                        'elapsed_time'     : 'bme280_elapsed_time'     ,
                                        'start_epoch_time' : 'bme280_start_epoch_time' ,
                                        'unix_epoch_time'  : 'bme280_unix_epoch_time'  ,
                                        'temperature'      : 'bme280_temperature'      ,
                                        'pressure'         : 'bme280_pressure'         ,
                                        'humidity'         : 'bme280_humidity'         ,
                                        'altitude'         : 'bme280_altitude'
                                    }
                                )
                            else:
                                match_row                             = match.rename(
                                    columns={
                                        'elapsed_time'     : 'bme280_elapsed_time'     ,
                                        'start_epoch_time' : 'bme280_start_epoch_time' ,
                                        'unix_epoch_time'  : 'bme280_unix_epoch_time'  ,
                                        'temperature'      : 'bme280_temperature'      ,
                                        'pressure'         : 'bme280_pressure'         ,
                                        'humidity'         : 'bme280_humidity'
                                    }
                                )
                            matchTolerance.append( match_row )
    
                        else:
                            empty_row = pandas.DataFrame( { col : [numpy.nan] for col in bme280DataFrame.columns } )
                            if self.__altitude_en:
                                empty_row = empty_row.rename(
                                    columns={
                                        'elapsed_time'     : 'bme280_elapsed_time'     ,
                                        'start_epoch_time' : 'bme280_start_epoch_time' ,
                                        'unix_epoch_time'  : 'bme280_unix_epoch_time'  ,
                                        'temperature'      : 'bme280_temperature'      ,
                                        'pressure'         : 'bme280_pressure'         ,
                                        'humidity'         : 'bme280_humidity'         ,
                                        'altitude'         : 'bme280_altitude'
                                    }
                                )
                            else:
                                empty_row = empty_row.rename(
                                    columns={
                                        'elapsed_time'     : 'bme280_elapsed_time'     ,
                                        'start_epoch_time' : 'bme280_start_epoch_time' ,
                                        'unix_epoch_time'  : 'bme280_unix_epoch_time'  ,
                                        'temperature'      : 'bme280_temperature'      ,
                                        'pressure'         : 'bme280_pressure'         ,
                                        'humidity'         : 'bme280_humidity'
                                    }
                                )

                            matchTolerance.append( empty_row )
                    concatDataFrame = pandas.concat( matchTolerance , ignore_index=True )
                    dataFrame = pandas.concat( [ dataFrame , concatDataFrame ] , axis=1 )
    
                if self.__mpu6050_csv is not None:
                    matchTolerance  = []
                    mpu6050DataFrame = pandas.read_csv( self.__mpu6050_csv )
                    for unix_epoch_time in dataFrame['unix_epoch_time']:
                        match = mpu6050DataFrame[
                            ( mpu6050DataFrame['unix_epoch_time'] >= unix_epoch_time - self.__tolerance ) &
                            ( mpu6050DataFrame['unix_epoch_time'] <= unix_epoch_time + self.__tolerance )
                        ].copy()
    
                        if not match.empty:
                            match['mpu6050_unix_epoch_time_delta'] = abs(match['unix_epoch_time'] - unix_epoch_time)
                            match                                 = match.loc[match['mpu6050_unix_epoch_time_delta'].idxmin()]
                            match                                 = match.to_frame().T
                            match_row                             = match.rename(
                                columns={
                                    'elapsed_time'     : 'mpu6050_elapsed_time'     ,
                                    'start_epoch_time' : 'mpu6050_start_epoch_time' ,
                                    'unix_epoch_time'  : 'mpu6050_unix_epoch_time'  ,
                                    'ax'               : 'mpu6050_ax'               ,
                                    'ay'               : 'mpu6050_ay'               ,
                                    'az'               : 'mpu6050_az'               ,
                                    'gx'               : 'mpu6050_gx'               ,
                                    'gy'               : 'mpu6050_gy'               ,
                                    'gz'               : 'mpu6050_gz'               ,
                                    'temperature'      : 'mpu6050_temperature'
                                }
                            )
                            matchTolerance.append( match_row )
    
                        else:
                            empty_row = pandas.DataFrame( { col : [numpy.nan] for col in mpu6050DataFrame.columns } )
                            empty_row = empty_row.rename(
                                columns={
                                    'elapsed_time'     : 'mpu6050_elapsed_time'     ,
                                    'start_epoch_time' : 'mpu6050_start_epoch_time' ,
                                    'unix_epoch_time'  : 'mpu6050_unix_epoch_time'  ,
                                    'ax'               : 'mpu6050_ax'               ,
                                    'ay'               : 'mpu6050_ay'               ,
                                    'az'               : 'mpu6050_az'               ,
                                    'gx'               : 'mpu6050_gx'               ,
                                    'gy'               : 'mpu6050_gy'               ,
                                    'gz'               : 'mpu6050_gz'               ,
                                    'temperature'      : 'mpu6050_temperature'
                                }
                            )
                            matchTolerance.append( empty_row )
                    concatDataFrame = pandas.concat( matchTolerance , ignore_index=True )
                    dataFrame = pandas.concat( [ dataFrame , concatDataFrame ] , axis=1 )
    
                if self.__mpu9250_csv is not None:
                    matchTolerance  = []
                    mpu9250DataFrame = pandas.read_csv( self.__mpu9250_csv )
                    for unix_epoch_time in dataFrame['unix_epoch_time']:
                        match = mpu9250DataFrame[
                            ( mpu9250DataFrame['unix_epoch_time'] >= unix_epoch_time - self.__tolerance ) &
                            ( mpu9250DataFrame['unix_epoch_time'] <= unix_epoch_time + self.__tolerance )
                        ].copy()
    
                        if not match.empty:
                            match['mpu9250_unix_epoch_time_delta'] = abs(match['unix_epoch_time'] - unix_epoch_time)
                            match                                 = match.loc[match['mpu9250_unix_epoch_time_delta'].idxmin()]
                            match                                 = match.to_frame().T
                            match_row                             = match.rename(
                                columns={
                                    'elapsed_time'     : 'mpu9250_elapsed_time'     ,
                                    'start_epoch_time' : 'mpu9250_start_epoch_time' ,
                                    'unix_epoch_time'  : 'mpu9250_unix_epoch_time'  ,
                                    'accel'            : 'mpu9250_accel'            ,
                                    'gyro'             : 'mpu9250_gyro'             ,
                                    'magnet'           : 'mpu9250_magnet'
                                }
                            )
                            matchTolerance.append( match_row )
    
                        else:
                            empty_row = pandas.DataFrame( { col : [numpy.nan] for col in mpu9250DataFrame.columns } )
                            empty_row = empty_row.rename(
                                columns={
                                    'elapsed_time'     : 'mpu9250_elapsed_time'     ,
                                    'start_epoch_time' : 'mpu9250_start_epoch_time' ,
                                    'unix_epoch_time'  : 'mpu9250_unix_epoch_time'  ,
                                    'accel'            : 'mpu9250_accel'            ,
                                    'gyro'             : 'mpu9250_gyro'             ,
                                    'magnet'           : 'mpu9250_magnet'
                                }
                            )
                            matchTolerance.append( empty_row )
                    concatDataFrame = pandas.concat( matchTolerance , ignore_index=True )
                    dataFrame = pandas.concat( [ dataFrame , concatDataFrame ] , axis=1 )

                if self.__icm20948_csv is not None:
                    matchTolerance  = []
                    icm20948DataFrame = pandas.read_csv( self.__icm20948_csv )
                    for unix_epoch_time in dataFrame['unix_epoch_time']:
                        match = icm20948DataFrame[
                            ( icm20948DataFrame['unix_epoch_time'] >= unix_epoch_time - self.__tolerance ) &
                            ( icm20948DataFrame['unix_epoch_time'] <= unix_epoch_time + self.__tolerance )
                        ].copy()
    
                        if not match.empty:
                            match['icm20948_unix_epoch_time_delta'] = abs(match['unix_epoch_time'] - unix_epoch_time)
                            match                                 = match.loc[match['icm20948_unix_epoch_time_delta'].idxmin()]
                            match                                 = match.to_frame().T
                            match_row                             = match.rename(
                                columns={
                                    'elapsed_time'     : 'icm20948_elapsed_time'     ,
                                    'start_epoch_time' : 'icm20948_start_epoch_time' ,
                                    'unix_epoch_time'  : 'icm20948_unix_epoch_time'  ,
                                    'ax'               : 'icm20948_ax'               ,
                                    'ay'               : 'icm20948_ay'               ,
                                    'az'               : 'icm20948_az'               ,
                                    'gx'               : 'icm20948_gx'               ,
                                    'gy'               : 'icm20948_gy'               ,
                                    'gz'               : 'icm20948_gz'               ,
                                    'mx'               : 'icm20948_mx'               ,
                                    'my'               : 'icm20948_my'               ,
                                    'mz'               : 'icm20948_mz'               ,
                                    'temperature'      : 'icm20948_temperature'
                                }
                            )
                            matchTolerance.append( match_row )
    
                        else:
                            empty_row = pandas.DataFrame( { col : [numpy.nan] for col in icm20948DataFrame.columns } )
                            empty_row = empty_row.rename(
                                columns={
                                    'elapsed_time'     : 'icm20948_elapsed_time'     ,
                                    'start_epoch_time' : 'icm20948_start_epoch_time' ,
                                    'unix_epoch_time'  : 'icm20948_unix_epoch_time'  ,
                                    'ax'               : 'icm20948_ax'               ,
                                    'ay'               : 'icm20948_ay'               ,
                                    'az'               : 'icm20948_az'               ,
                                    'gx'               : 'icm20948_gx'               ,
                                    'gy'               : 'icm20948_gy'               ,
                                    'gz'               : 'icm20948_gz'               ,
                                    'mx'               : 'icm20948_mx'               ,
                                    'my'               : 'icm20948_my'               ,
                                    'mz'               : 'icm20948_mz'               ,
                                    'temperature'      : 'icm20948_temperature'
                                }
                            )
                            matchTolerance.append( empty_row )
                    concatDataFrame = pandas.concat( matchTolerance , ignore_index=True )
                    dataFrame = pandas.concat( [ dataFrame , concatDataFrame ] , axis=1 )

                if self.__gps_csv is not None:
                    matchTolerance  = []
                    gpsDataFrame = pandas.read_csv( self.__gps_csv )
                    for unix_epoch_time in dataFrame['unix_epoch_time']:
                        match = gpsDataFrame[
                            ( gpsDataFrame['unix_epoch_time'] >= unix_epoch_time - self.__tolerance_gps ) &
                            ( gpsDataFrame['unix_epoch_time'] <= unix_epoch_time + self.__tolerance_gps )
                        ].copy()
    
                        if not match.empty:
                            match['gps_unix_epoch_time_delta'] = abs(match['unix_epoch_time'] - unix_epoch_time)
                            match                              = match.loc[match['gps_unix_epoch_time_delta'].idxmin()]
                            match                              = match.to_frame().T
                            match_row                          = match.rename(
                                columns={
                                    'elapsed_time'       : 'gps_elapsed_time'       ,
                                    'start_epoch_time'   : 'gps_start_epoch_time'   ,
                                    'unix_epoch_time'    : 'gps_unix_epoch_time'    ,
                                    'latitude'           : 'gps_latitude'           ,
                                    'longitude'          : 'gps_longitude'          ,
                                    'altitude'           : 'gps_altitude'           ,
                                    'num_sats'           : 'gps_num_sats'           ,
                                    'datestam'           : 'gps_datestam'           ,
                                    'timestamp'          : 'gps_timestamp'          ,
                                    'spd_over_grnd'      : 'gps_spd_over_grnd'      ,
                                    'true_course'        : 'gps_true_course'        ,
                                    'true_track'         : 'gps_true_track'         ,
                                    'spd_over_grnd_kmph' : 'gps_spd_over_grnd_kmph' ,
                                    'pdop'               : 'gps_pdop'               ,
                                    'hdop'               : 'gps_hdop'               ,
                                    'vdop'               : 'gps_vdop'               ,
                                    'num_sv_in_view'     : 'gps_num_sv_in_view'
                                }
                            )
                            matchTolerance.append( match_row )
    
                        else:
                            empty_row = pandas.DataFrame( { col : [numpy.nan] for col in gpsDataFrame.columns } )
                            empty_row = empty_row.rename(
                                columns={
                                    'elapsed_time'       : 'gps_elapsed_time'       ,
                                    'start_epoch_time'   : 'gps_start_epoch_time'   ,
                                    'unix_epoch_time'    : 'gps_unix_epoch_time'    ,
                                    'latitude'           : 'gps_latitude'           ,
                                    'longitude'          : 'gps_longitude'          ,
                                    'altitude'           : 'gps_altitude'           ,
                                    'num_sats'           : 'gps_num_sats'           ,
                                    'datestam'           : 'gps_datestam'           ,
                                    'timestamp'          : 'gps_timestamp'          ,
                                    'spd_over_grnd'      : 'gps_spd_over_grnd'      ,
                                    'true_course'        : 'gps_true_course'        ,
                                    'true_track'         : 'gps_true_track'         ,
                                    'spd_over_grnd_kmph' : 'gps_spd_over_grnd_kmph' ,
                                    'pdop'               : 'gps_pdop'               ,
                                    'hdop'               : 'gps_hdop'               ,
                                    'vdop'               : 'gps_vdop'               ,
                                    'num_sv_in_view'     : 'gps_num_sv_in_view'
                                }
                            )
                            matchTolerance.append( empty_row )
                    concatDataFrame = pandas.concat( matchTolerance , ignore_index=True )
                    dataFrame       = pandas.concat( [ dataFrame , concatDataFrame ] , axis=1 )
                
            if self.__excel_en:
                self.__output_to_excel( "movie" , basename + "_analyse.xlsx" , dataFrame )
                #dataFrame.to_excel(  basename + "_analyse.xlsx" , index=False )
            else:
                dataFrame.to_csv  (  basename + "_analyse.csv"  , index=False )

            if self.__movieFile is not None:
                self.__movie_gen( dataFrame )

    def __movie_gen( self , dataFrame ):
        print("[Info] Start the __movie_gen function.")
        os.makedirs( './tmp' , exist_ok=True )
        self.__separation_h264_to_jpeg( self.__movieFile )
        cap       = cv2.VideoCapture( self.__movieFile )
        framerate = cap.get( cv2.CAP_PROP_FPS )
        self.__add_sensor_frame( dataFrame , framerate )
        self.__merge_jpeg_to_h264( self.__movieFile + ".sensor.h264" , str(framerate) )
        self.__convert_h264_to_mp4( self.__movieFile + ".sensor.h264" )
        shutil.rmtree('./tmp')  

    def __separation_h264_to_jpeg( self , movieFileName ):
        print("[Info] Start the __separation_h264_to_jpeg function.")
        if shutil.which("ffmpeg") is not None:
            print("[Info] ffmpeg -i " + movieFileName + " -qscale:v 2 tmp/frame_%08d.jpg")
            subprocess.run(
                "ffmpeg -i " + movieFileName +
                " -qscale:v 2 tmp/frame_%08d.jpg" ,
                shell          = True ,
                capture_output = True ,
                text           = True
            )
        else:
            print("[Warn] apt install -y ffmpeg")        

    def __add_sensor_frame( self , dataFrame , framerate ):
        print("[Info] Start the __add_sensor_frame function.")
        imgFiles = sorted(glob.glob('tmp/frame_*.jpg'))
        frame_index = 0
        for imgFile in imgFiles:
            image    = cv2.imread(imgFile)
            text     =        "DATE                   : " + str( dataFrame.iloc[frame_index]['current_time']       ) + "\n"
            text     = text + "FRAMERATE             : " + str( framerate                                         ) + "\n"
            if self.__bme280_csv  is not None:
                if self.__altitude_en:
                    text = text + "ALTITUDE               : " + str( dataFrame.iloc[frame_index]['bme280_altitude'] ) + "\n"
                text = text + "BME280 TEMPERATURE : " + str( dataFrame.iloc[frame_index]['bme280_temperature'] ) + "\n"
                text = text + "BME280 PRESSURE     : " + str( dataFrame.iloc[frame_index]['bme280_pressure']    ) + "\n"
                text = text + "BME280 HUMIDLY       : " + str( dataFrame.iloc[frame_index]['bme280_humidity']    ) + "\n"
            if self.__mpu6050_csv is not None:
                text = text + "MPU6050 AX           : " + str( dataFrame.iloc[frame_index]['mpu6050_ax']         ) + "\n"
                text = text + "MPU6050 AY           : " + str( dataFrame.iloc[frame_index]['mpu6050_ay']         ) + "\n"
                text = text + "MPU6050 AZ           : " + str( dataFrame.iloc[frame_index]['mpu6050_az']         ) + "\n"
                text = text + "MPU6050 GX           : " + str( dataFrame.iloc[frame_index]['mpu6050_gx']         ) + "\n"
                text = text + "MPU6050 GY           : " + str( dataFrame.iloc[frame_index]['mpu6050_gy']         ) + "\n"
                text = text + "MPU6050 GZ           : " + str( dataFrame.iloc[frame_index]['mpu6050_gz']         ) + "\n"
            if self.__mpu9250_csv is not None:
                text = text + "MPU9250 ACCEL        : " + str( dataFrame.iloc[frame_index]['mpu9250_accel']      ) + "\n"
                text = text + "MPU9250 GYRO         : " + str( dataFrame.iloc[frame_index]['mpu9250_gyro']       ) + "\n"
                text = text + "MPU9250 MAGNET       : " + str( dataFrame.iloc[frame_index]['mpu9250_magnet']     ) + "\n"
            if self.__icm20948_csv is not None:
                text = text + "ICM20948 AX           : " + str( dataFrame.iloc[frame_index]['icm20948_ax']         ) + "\n"
                text = text + "ICM20948 AY           : " + str( dataFrame.iloc[frame_index]['icm20948_ay']         ) + "\n"
                text = text + "ICM20948 AZ           : " + str( dataFrame.iloc[frame_index]['icm20948_az']         ) + "\n"
                text = text + "ICM20948 GX           : " + str( dataFrame.iloc[frame_index]['icm20948_gx']         ) + "\n"
                text = text + "ICM20948 GY           : " + str( dataFrame.iloc[frame_index]['icm20948_gy']         ) + "\n"
                text = text + "ICM20948 GZ           : " + str( dataFrame.iloc[frame_index]['icm20948_gz']         ) + "\n"
                text = text + "ICM20948 MX           : " + str( dataFrame.iloc[frame_index]['icm20948_mx']         ) + "\n"
                text = text + "ICM20948 MY           : " + str( dataFrame.iloc[frame_index]['icm20948_my']         ) + "\n"
                text = text + "ICM20948 MZ           : " + str( dataFrame.iloc[frame_index]['icm20948_mz']         ) + "\n"
            if self.__gps_csv is not None:
                text = text + "GPS LATITUDE           : " + str( dataFrame.iloc[frame_index]['gps_latitude']           ) + "\n"
                text = text + "GPS LONGITUDE          : " + str( dataFrame.iloc[frame_index]['gps_longitude']          ) + "\n"
                text = text + "GPS ALTITUDE           : " + str( dataFrame.iloc[frame_index]['gps_altitude']           ) + "\n"
                text = text + "GPS NUM_SATS           : " + str( dataFrame.iloc[frame_index]['gps_num_sats']           ) + "\n"
                text = text + "GPS DATESTAM           : " + str( dataFrame.iloc[frame_index]['gps_datestam']           ) + "\n"
                text = text + "GPS TIMESTAMP          : " + str( dataFrame.iloc[frame_index]['gps_timestamp']          ) + "\n"
                text = text + "GPS SPD OVER GRND      : " + str( dataFrame.iloc[frame_index]['gps_spd_over_grnd']      ) + "\n"
                text = text + "GPS TRUE COURSE        : " + str( dataFrame.iloc[frame_index]['gps_true_course']        ) + "\n"
                text = text + "GPS TRUE TRACK         : " + str( dataFrame.iloc[frame_index]['gps_true_track']         ) + "\n"
                text = text + "GPS SPD OVER GRND KMPH : " + str( dataFrame.iloc[frame_index]['gps_spd_over_grnd_kmph'] ) + "\n"
                text = text + "GPS PDOP               : " + str( dataFrame.iloc[frame_index]['gps_pdop']               ) + "\n"
                text = text + "GPS HDOP               : " + str( dataFrame.iloc[frame_index]['gps_hdop']               ) + "\n"
                text = text + "GPS VDOP               : " + str( dataFrame.iloc[frame_index]['gps_vdop']               ) + "\n"
                text = text + "GPS NUM SV IN VIEW     : " + str( dataFrame.iloc[frame_index]['gps_num_sv_in_view']     ) + "\n"
                
            x , y       = 10 , 30
            #font        = cv2.FONT_HERSHEY_SIMPLEX
            font        = cv2.FONT_HERSHEY_PLAIN
            font_scale  = 1.5
            color       = ( 0 , 255 , 0 )
            thickness   = 1
            line_height = 30
            for i, line in enumerate(text.split('\n')):
                y_pos = y + i * line_height
                cv2.putText( image , line , (x, y_pos) , font , font_scale , color , thickness , cv2.LINE_AA )
            cv2.imwrite( str(re.sub(r"frame_", "frame_opencv_", imgFile )) , image)
            frame_index = frame_index + 1
            
    def __merge_jpeg_to_h264( self , movieFileName , framerate ):
        print("[Info] Start the __merge_jpeg_to_h264 function.")
        if shutil.which("ffmpeg") is not None:
            print(
                "[Info] ffmpeg -framerate " + str(framerate) +
                " -i tmp/frame_opencv_%08d.jpg -c:v libx264 -f h264 -y " + movieFileName
            )
            subprocess.run(
                "ffmpeg -framerate " + str(framerate) +
                " -i tmp/frame_opencv_%08d.jpg -c:v libx264 -f h264 -y " + movieFileName ,
                shell          = True ,
                capture_output = True ,
                text           = True
            )
        else:
            print("[Warn] Install it with the following command.")
            print("[Warn] apt install -y ffmpeg")
            
    def doSensorAnalyzerImplImpl( self ):
        print("[Info] Start the doSensorAnalyzerImplImpl function.")
        try:
            threadList = []
            bme280DataFrame = None
            if self.__mp4_en:
                threadList.append( threading.Thread
                    ( args=( self.__movieFile , ) , target=self.__convert_h264_to_mp4 )
                )
            if self.__altitude_en:
                bme280DataFrame = self.__generate_alititude_csv()
            if self.__icm20948_csv is not None:
                pass
            if self.__gps_csv is not None:
                threadList.append( threading.Thread( target=self.__generate_map_html      ) )
                threadList.append( threading.Thread( target=self.__generate_map_kml       ) )
            if self.__bme280_graph_en  :
                threadList.append( threading.Thread( target=self.__generate_bme280_graph  ) )
            if self.__mpu6050_graph_en :
                threadList.append( threading.Thread( target=self.__generate_mpu6050_graph ) )
            if self.__mpu9250_graph_en :
                threadList.append( threading.Thread( target=self.__generate_mpu9250_graph ) )
            if self.__frame_sync_en    :
                threadList.append(
                    threading.Thread( args   = ( bme280DataFrame , )  , target = self.__analyse_frame_sync )
                )
            for signleThread in threadList:
                signleThread.start()
            for signleThread in threadList:
                signleThread.join()
        except Exception as e:
            print(e)

########################################################################

def main(argv):
    print("[Info] Start the main function.")
    sw = SensorWrapper( argv )
    sw.doSensorWrapper()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
