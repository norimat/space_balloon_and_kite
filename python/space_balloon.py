#!/usr/bin/env python
try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
    import smbus2
    import bme280
    import qwiic_icm20948
    import qwiic_i2c
    import serial
    import pynmea2
except ImportError:
    print("[Warn] The libraries required for reading sensor data from GPIO or related interfaces have not been imported.")

import math
import folium
from folium.plugins import TimestampedGeoJson
import simplekml
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

    start_unix_epoch_time = 0.0
    bme280_cond           = threading.Condition()
    mpu6050_cond          = threading.Condition()
    icm20948_cond         = threading.Condition()
    camera_module_cond    = threading.Condition()
    powermonitor_cond     = threading.Condition()
    running               = threading.Event()
    bme280_ready          = False
    mpu6050_ready         = False
    icm20948_ready        = False
    camera_module_ready   = False
    powermonitor_ready    = False

    def __init__( self , argv ):
        print("[Info] Create an instance of the SensorWrapper class.")
        self.argv                    = argv
        self.__bme280_bus            = None
        self.__mpu6050_bus           = None
        self.__camera_fa             = None
        self.__bme280_fa             = None
        self.__mpu6050_fa            = None
        self.__icm20948_fa           = None
        self.__powermonitor_fa       = None
        self.__gps_fa                = None
        self.__mode                  = None
        self.__output_dir            = None
        self.__icm20948_i2cbus       = None
        self.__bme280_i2cbus         = None
        self.__mpu6050_i2cbus        = None
        self.__gps_en                = None
        self.__powermonitor_en       = None
        self.__bme280_en             = None
        self.__mpu6050_en            = None
        self.__icm20948_en           = None
        self.__framerate             = None
        self.__bitrate               = None
        self.__width                 = None
        self.__height                = None
        self.__gps_port              = None
        self.__bme280_addr           = None
        self.__mpu6050_addr          = None
        self.__icm20948_addr         = None
        self.__gps_csv               = None
        self.__bme280_csv            = None
        self.__mpu6050_csv           = None
        self.__icm20948_csv          = None
        self.__gps_interval          = None
        self.__mp4_en                = None
        self.__altitude_en           = None
        self.__bme280_graph          = None
        self.__mpu6050_graph         = None
        self.__icm20948_graph        = None
        self.__tolerance             = None
        self.__tolerance_gps         = None
        self.__excel_en              = None
        self.__map_animation_en      = None
       
    def __handler( self , signum , frame ):
        SensorWrapper.running.clear()
        self.__camera_fa       .close()
        self.__bme280_en       and self.__bme280_fa       .close()
        self.__mpu6050_en      and self.__mpu6050_fa      .close()
        self.__icm20948_en     and self.__icm20948_fa     .close()
        self.__powermonitor_en and self.__powermonitor_fa .close()
        self.__gps_en          and self.__gps_fa          .close()
        self.__bme280_bus      .close()
        self.__mpu6050_bus     .close()
        SensorWrapper.camera_module_ready = True
        SensorWrapper.bme280_ready        = True
        SensorWrapper.mpu6050_ready       = True
        SensorWrapper.icm20948_ready      = True
        SensorWrapper.powermonitor_ready  = True
        SensorWrapper.bme280_cond              .notify()
        SensorWrapper.runningmpu6050_cond      .notify()
        SensorWrapper.runningicm20948_cond     .notify()
        SensorWrapper.runningcamera_module_cond.notify()
        SensorWrapper.runningpowermonitor_cond .notify()
        shutil.rmtree( './tmp' , ignore_errors=True )

    def __garbage_colloction( self ):
        pass

    def __generate_empty_csvFile( self , csvFileName , data ):
        print("[Info] Create the  " + csvFileName + ".")
        fopen  = open( csvFileName , 'w' , newline='' , encoding='utf-8' )
        writer = csv.writer( fopen )
        writer.writerows( data )
        fopen.close()

    def __get_csvFile( self , csvFileName ):
        fappend = open( csvFileName , 'a' , newline='' , encoding='utf-8' , buffering=65536 )
        return fappend

    def __read_args( self ):
        parser = argparse.ArgumentParser( description='option' , formatter_class=argparse.RawTextHelpFormatter )
        parser.add_argument( '--mode'       , '-m' , default=0     , required=True       , help="" )
        #############################################################################################
        # Sensor Acquisition Mode Options
        parser.add_argument( '--output_dir'     , '-o' , default="./"                        , help="" )       
        parser.add_argument( '--gps'                   , default=False , action='store_true' , help="" )
        parser.add_argument( '--bme280'                , default=False , action='store_true' , help="" )
        parser.add_argument( '--mpu6050'               , default=False , action='store_true' , help="" )
        parser.add_argument( '--icm20948'              , default=False , action='store_true' , help="" )
        parser.add_argument( '--powermonitor'          , default=False , action='store_true' , help="" ) 
        parser.add_argument( '--icm20948_i2cbus'       , default=1                           , help="" )
        parser.add_argument( '--bme280_i2cbus'         , default=1                           , help="" )
        parser.add_argument( '--mpu6050_i2cbus'        , default=1                           , help="" )
        parser.add_argument( '--framerate'             , default="30"                        , help="" )
        parser.add_argument( '--bitrate'               , default="8000000"                   , help="" )
        parser.add_argument( '--width'                 , default="1920"                      , help="" )
        parser.add_argument( '--height'                , default="1080"                      , help="" )       
        parser.add_argument( '--gps_port'              , default="/dev/ttyACM0"              , help="" )
        parser.add_argument( '--gps_interval'          , default="1.0"                       , help="" )
        parser.add_argument( '--bme280_addr'           , default="0x76"                      , help="" )
        parser.add_argument( '--mpu6050_addr'          , default="0x68"                      , help="" )
        parser.add_argument( '--icm20948_addr'         , default="0x68"                      , help="" )
        #############################################################################################
        # Sensor Data Analysis Mode Options
        parser.add_argument( '--frame_sync'            , default=False , action='store_true' , help="" )
        parser.add_argument( '--movie_csv'                                                   , help="" )
        parser.add_argument( '--gps_csv'                                                     , help="" )
        parser.add_argument( '--bme280_csv'                                                  , help="" )
        parser.add_argument( '--mpu6050_csv'                                                 , help="" )
        parser.add_argument( '--icm20948_csv'                                                , help="" )
        parser.add_argument( '--mp4'                   , default=False , action='store_true' , help="" )
        parser.add_argument( '--altitude'              , default=False , action='store_true' , help="" )
        parser.add_argument( '--bme280_graph'          , default=False , action='store_true' , help="" )
        parser.add_argument( '--mpu6050_graph'         , default=False , action='store_true' , help="" )
        parser.add_argument( '--icm20948_graph'        , default=False , action='store_true' , help="" )
        parser.add_argument( '--movie'                                                       , help="" )
        parser.add_argument( '--tolerance'             , default=0.032                       , help="" )
        parser.add_argument( '--tolerance_gps'         , default=1                           , help="" )
        parser.add_argument( '--excel'                 , default=False , action='store_true' , help="" )
        parser.add_argument( '--map_animation'         , default=False , action='store_true' , help="" )
        #############################################################################################

        try:
            ############################################################
            args                         = parser.parse_args()
            self.__mode                  = int   ( args.mode                  )
            self.__output_dir            =         args.output_dir
            self.__gps_en                = int   ( args.gps                   )
            self.__bme280_en             = int   ( args.bme280                )
            self.__mpu6050_en            = int   ( args.mpu6050               )
            self.__icm20948_en           = int   ( args.icm20948              )
            self.__powermonitor_en       = int   ( args.powermonitor          )
            self.__icm20948_i2cbus       = int   ( args.icm20948_i2cbus       )
            self.__bme280_i2cbus         = int   ( args.bme280_i2cbus         )
            self.__mpu6050_i2cbus        = int   ( args.mpu6050_i2cbus        )
            self.__framerate             = int   ( args.framerate             )
            self.__gps_interval          = float ( args.gps_interval          )
            self.__bitrate               = int   ( args.bitrate               )
            self.__width                 = int   ( args.width                 )
            self.__height                = int   ( args.height                )
            self.__gps_port              =         args.gps_port
            self.__bme280_addr           = int   ( args.bme280_addr   , 16    )
            self.__mpu6050_addr          = int   ( args.mpu6050_addr  , 16    )
            self.__icm20948_addr         = int   ( args.icm20948_addr , 16    )
            self.__movie_csv             =         args.movie_csv
            self.__gps_csv               =         args.gps_csv
            self.__bme280_csv            =         args.bme280_csv
            self.__mpu6050_csv           =         args.mpu6050_csv
            self.__icm20948_csv          =         args.icm20948_csv
            self.__frame_sync_en         = int   ( args.frame_sync            )
            self.__mp4_en                = int   ( args.mp4                   )
            self.__altitude_en           = int   ( args.altitude              )
            self.__bme280_graph_en       = int   ( args.bme280_graph          )
            self.__mpu6050_graph_en      = int   ( args.mpu6050_graph         )
            self.__icm20948_graph_en     = int   ( args.icm20948_graph        )
            self.__movieFile             =         args.movie
            self.__tolerance             = float ( args.tolerance             )
            self.__tolerance_gps         = float ( args.tolerance_gps         )
            self.__excel_en              = int   ( args.excel                 )
            self.__map_animation_en      = int   ( args.map_animation         )
            ############################################################
        except Exception as e:
            print(e)
            sys.exit(1)

    def __setup_sensors( self ):
        print("[Info] Start the __generate_empty_csvFile function.")
        csvUnixEpochTimeStr  = str( time.time() )
        timestamp            = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_timestamp_dir = self.__output_dir + "/" + timestamp
        os.makedirs( self.__output_dir    , exist_ok=True )
        os.makedirs( output_timestamp_dir , exist_ok=True )
        bme280CsvFile       = output_timestamp_dir + "/bme280"       + ".csv"
        mpu6050CsvFile      = output_timestamp_dir + "/mpu6050"      + ".csv"
        icm20948CsvFile     = output_timestamp_dir + "/icm20948"     + ".csv"
        cameraCsvFile       = output_timestamp_dir + "/movie"        + ".csv"
        gpsCsvFile          = output_timestamp_dir + "/gps"          + ".csv"
        powermonitorCsvFile = output_timestamp_dir + "/powermonitor" + ".csv"
        movieFileName       = output_timestamp_dir + "/movie"        + ".h264"

        if self.__bme280_i2cbus == self.__mpu6050_i2cbus:
            self.__bme280_bus   = smbus2.SMBus( self.__bme280_i2cbus  )
            self.__mpu6050_bus  = self.__bme280_bus
        else:
            self.__bme280_bus   = smbus2.SMBus( self.__bme280_i2cbus  )
            self.__mpu6050_bus  = smbus2.SMBus( self.__mpu6050_i2cbus )

        #########################################################################
        print("[Info] Activate the Camera Module.")
        data = [
            [
                'camera_module_elapsed_time' , 'camera_module_start_epoch_time' , 'camera_unix_epoch_time' ,
                'frame_count'
            ]
        ]
        self.__generate_empty_csvFile( cameraCsvFile , data )
        self.__camera_fa  = self.__get_csvFile( cameraCsvFile )
        self.__cameraModuleImpl = CameraModuleImpl(
            cameraCsvFile     ,
            self.__camera_fa  ,
            movieFileName     ,
            self.__framerate  ,
            self.__bitrate    ,
            self.__width      ,
            self.__height
        )
        #########################################################################
        if self.__icm20948_en :
            print("[Info] Activate the ICM-20948.")
            data = [
                [
                    'icm-20948_elapsed_time' , 'icm-20948_start_epoch_time' , 'icm-20948_unix_epoch_time' ,
                    'icm-20948_ax' , 'icm-20948_ay' , 'icm-20948_az' ,
                    'icm-20948_gx' , 'icm-20948_gy' , 'icm-20948_gz' ,
                    'icm-20948_mx' , 'icm-20948_my' , 'icm-20948_mz' ,
                    'icm-20948_temperature'
                ]
            ]
            self.__generate_empty_csvFile( icm20948CsvFile , data )
            self.__icm20948_fa  = self.__get_csvFile( icm20948CsvFile )
            self.__icm20948Impl = ICM20948Impl( self.__icm20948_addr , self.__icm20948_i2cbus , self.__icm20948_fa )
        #########################################################################
        if self.__bme280_en :
            print("[Info] Activate the BME280.")
            data = [
                [
                    'bme280_elapsed_time' , 'bme280_start_epoch_time' , 'bme280_unix_epoch_time' ,
                    'bme280_byte_00' , 'bme280_byte_01' , 'bme280_byte_02' , 'bme280_byte_03' ,
                    'bme280_byte_04' , 'bme280_byte_05' , 'bme280_byte_06' , 'bme280_byte_07' ,
                    'bme280_byte_08' , 'bme280_byte_09' , 'bme280_byte_10' , 'bme280_byte_11' ,
                    'bme280_byte_12' , 'bme280_byte_13' , 'bme280_byte_14' , 'bme280_byte_15' ,
                    'bme280_byte_16' , 'bme280_byte_17' , 'bme280_byte_18' , 'bme280_byte_19' ,
                    'bme280_byte_20' , 'bme280_byte_21' , 'bme280_byte_22' , 'bme280_byte_23' ,
                    'bme280_byte_24' , 'bme280_byte_25' , 'bme280_byte_26' , 'bme280_byte_27' ,
                    'bme280_byte_28' , 'bme280_byte_29' , 'bme280_byte_30' , 'bme280_byte_31' ,
                    'bme280_byte_32' , 'bme280_byte_33' , 'bme280_byte_34' , 'bme280_byte_35' ,
                    'bme280_byte_36' , 'bme280_byte_37' , 'bme280_byte_38' , 'bme280_byte_39'
                ]
            ]
            self.__generate_empty_csvFile( bme280CsvFile , data )
            self.__bme280_fa  = self.__get_csvFile( bme280CsvFile )
            self.__bme280Impl = BME280Impl( self.__bme280_bus , self.__bme280_addr , self.__bme280_fa )
        #########################################################################
        if self.__mpu6050_en:
            print("[Info] Activate the MPU6050.")
            data = [
                [
                    'mpu6050_elapsed time' , 'mpu6050_start_epoch_time' , 'mpu6060_unix_epoch_time' ,
                    'mpu6050_byte_00' , 'mpu6050_byte_01' , 'mpu6050_byte_02' ,
                    'mpu6050_byte_03' , 'mpu6050_byte_04' , 'mpu6050_byte_05' ,
                    'mpu6050_byte_06' , 'mpu6050_byte_07' , 'mpu6050_byte_08' ,
                    'mpu6050_byte_09' , 'mpu6050_byte_10' , 'mpu6050_byte_11' ,
                    'mpu6050_byte_12' , 'mpu6050_byte_13'                
                ]
            ]
            self.__generate_empty_csvFile( mpu6050CsvFile , data )
            self.__mpu6050_fa  = self.__get_csvFile( mpu6050CsvFile )
            self.__mpu6050Impl = MPU6050Impl( self.__mpu6050_bus , self.__mpu6050_addr , self.__mpu6050_fa )
        #########################################################################
        if self.__gps_en :
            print("[Info] Activate the IVK172 G-Mouse USB GPS.")
            data = [
                [
                    'ivk172_elapsed_time' , 'ivk172_start_epoch_time' , 'ivk172_unix_epoch_time' ,
                    'ivk172_latitude'       , 'ivk172_longitude'          , 'ivk172_altitude'       ,
                    'ivk172_altitude_units' , 'ivk172_num_sats'           , 'ivk172_datestam'       ,
                    'ivk172_timestamp'      , 'ivk172_spd_over_grnd'      , 'ivk172_true_course'    ,
                    'ivk172_true_track'     , 'ivk172_spd_over_grnd_kmph' , 'ivk172_pdop'           ,
                    'ivk172_hdop'           , 'ivk172_vdop'               , 'ivk172_num_sv_in_view'
                ]
            ]
            self.__generate_empty_csvFile( gpsCsvFile , data )
            self.__gps_fa = self.__get_csvFile( gpsCsvFile )
            self.__gpsModuleImpl = GPSModuleImpl( self.__gps_port , self.__gps_fa , self.__gps_interval )
        #########################################################################
        if self.__powermonitor_en :
            print("[Info] Activate the PowerMonitor.")
            data = [
                [
                    'power_monitor_elapsed_time' , 'power_monitor_start_epoch_time' , 'power_monitor_unix_epoch_time' ,
                    'voltage' , 'throttled_status'
                ]
            ]
            self.__generate_empty_csvFile( powermonitorCsvFile , data )
            self.__powermonitor_fa = self.__get_csvFile( powermonitorCsvFile )
            self.__powermonitorImpl = PowerMonitorImpl( self.__powermonitor_fa )
        #########################################################################
                
    def doSensorWrapper(self):
        print("[Info] Start the doSensorWrapper function.")
        self.__read_args()
        signal.signal( signal.SIGINT , self.__handler )
        #######################################################################
        if self.__mode == 0:
            print("[Info] It operates in sensor data output mode.")
            self.__setup_sensors()
            threadList = []
            try:
                threadList.append( threading.Thread(                            target=self.__cameraModuleImpl.doCameraModuleImpl ) )
                self.__gps_en          and threadList.append( threading.Thread( target=self.__gpsModuleImpl   .doGpsModuleImpl    ) )
                self.__bme280_en       and threadList.append( threading.Thread( target=self.__bme280Impl      .doBME280Impl       ) )
                self.__mpu6050_en      and threadList.append( threading.Thread( target=self.__mpu6050Impl     .doMPU6050Impl      ) )
                self.__icm20948_en     and threadList.append( threading.Thread( target=self.__icm20948Impl    .doIcm20948Impl     ) )
                self.__powermonitor_en and threadList.append( threading.Thread( target=self.__powermonitorImpl.doPowerMonitorImpl ) )
                SensorWrapper.running.set()
                for singleThread in threadList:
                    singleThread.start()
                self.__garbage_colloction() # GC
                for singleThread in threadList:
                    singleThread.join()
            except Exception as e:
                print(e)
        #######################################################################
        elif self.__mode == 1:
            print("[Info] It operates in sensor data reading and analysis mode.")
            sai = SensorAnalyzerImpl(
                self.__movieFile        ,
                self.__mp4_en           ,
                self.__altitude_en      ,
                self.__bme280_graph_en  ,
                self.__mpu6050_graph_en ,
                self.__icm20948_graph   ,
                self.__frame_sync_en    ,
                self.__gps_csv          ,
                self.__bme280_csv       ,
                self.__mpu6050_csv      ,
                self.__icm20948_csv     ,
                self.__movie_csv        ,
                self.__tolerance        ,
                self.__tolerance_gps    ,
                self.__excel_en         ,
                self.__map_animation_en
            )
            sai.doSensorAnalyzerImplImpl()
        #######################################################################

########################################################################
class PowerMonitorImpl:

    def __init__( self , csvFile ):
        print("[Info] Create an instance of the PowerMonitorImpl class.")
        self.__csvFileWriter = csv.writer( csvFile )

    def __get_voltage(self):
        try:
            out = subprocess.check_output(['vcgencmd', 'measure_volts']).decode()
            return float(out.split('=')[1].replace('V', '').strip())
        except Exception as e:
            print(f"[Error] get_voltage(): {e}")
            return None

    def __get_throttled(self):
        try:
            out = subprocess.check_output(['vcgencmd', 'get_throttled']).decode()
            return out.strip().split('=')[1]
        except Exception as e:
            print(e)
            return None

    def doPowerMonitorImpl(self):
        print("[Info] Start the doPowerMonitorImpl function.")
        while SensorWrapper.running.is_set():
            try:
                SensorWrapper.powermonitor_cond.acquire()
                while not SensorWrapper.powermonitor_ready:
                    SensorWrapper.powermonitor_cond.wait()
                SensorWrapper.powermonitor_cond.release()

                voltage             = self.__get_voltage()
                throttled           = self.__get_throttled()
                end_unix_epoch_time = time.time()
                total_time          = end_unix_epoch_time - SensorWrapper.start_unix_epoch_time
                data = [
                    [
                        total_time , SensorWrapper.start_unix_epoch_time , end_unix_epoch_time ,
                        voltage , throttled
                    ]
                ]
                self.__csvFileWriter.writerows( data )
                SensorWrapper.powermonitor_ready = False
            except (KeyboardInterrupt , ValueError) as e:
                SensorWrapper.running.clear()
            except Exception as e:
                print(e)
        
########################################################################
class BME280Impl:

    def __init__( self , bus , address , csvFile ):
        print("[Info] Create an instance of the BME280Impl class.")
        print("[Info] The device address of the BME280 is " + str(hex(address)) )
        self.__csvFileWriter = csv.writer( csvFile )
        self.__address       = address
        self.__bus           = bus

    def __read_sensor(self):
        self.__bus.write_byte_data( self.__address , 0xF2 , 0x01 )  # Humidity oversampling x1                   
        self.__bus.write_byte_data( self.__address , 0xF4 , 0x27 )  # Normal mode, temp/press oversampling x1    
        self.__bus.write_byte_data( self.__address , 0xF5 , 0xA0 )  # Config
        read24byte    = self.__bus.read_i2c_block_data ( self.__address , 0x88 , 24 )
        read1Byte0xA1 = self.__bus.read_byte_data      ( self.__address , 0xA1      )
        read7byte     = self.__bus.read_i2c_block_data ( self.__address , 0xE1 ,  7 )
        read8byte     = self.__bus.read_i2c_block_data ( self.__address , 0xF7 ,  8 )
        return read24byte , read1Byte0xA1 , read7byte , read8byte

    def doBME280Impl(self):
        print("[Info] Start the doBME280Impl function.")
        try:
            while SensorWrapper.running.is_set():
                SensorWrapper.bme280_cond.acquire()
                while not SensorWrapper.bme280_ready:
                    SensorWrapper.bme280_cond.wait()
                SensorWrapper.bme280_cond.release()

                read24byte , read1Byte0xA1 , read7byte , read8byte = self.__read_sensor()
                end_unix_epoch_time = time.time()
                total_time          = end_unix_epoch_time - SensorWrapper.start_unix_epoch_time
                data = [
                    [
                        total_time , SensorWrapper.start_unix_epoch_time , end_unix_epoch_time ,
                        read24byte[ 0] , read24byte[ 1], read24byte[ 2], read24byte[ 3],
                        read24byte[ 4] , read24byte[ 5], read24byte[ 6], read24byte[ 7],
                        read24byte[ 8] , read24byte[ 9], read24byte[10], read24byte[11],
                        read24byte[12] , read24byte[13], read24byte[14], read24byte[15],
                        read24byte[16] , read24byte[17], read24byte[18], read24byte[19],
                        read24byte[20] , read24byte[21], read24byte[22], read24byte[23],
                        read1Byte0xA1  , read7byte[0] , read7byte[1] , read7byte[2] ,
                        read7byte[3]   , read7byte[4] , read7byte[5] , read7byte[6] ,
                        read8byte[0] , read8byte[1] , read8byte[2] , read8byte[3] ,
                        read8byte[4] , read8byte[5] , read8byte[6] , read8byte[7]
                    ]
                ]
                self.__csvFileWriter.writerows( data )
                SensorWrapper.bme280_ready = False
        except (KeyboardInterrupt , ValueError) as e:
            SensorWrapper.running.clear()
        except Exception as e:
            print(e)

########################################################################
class MPU6050Impl:

    def __init__( self , bus , address , csvFile ):
        print("[Info] Create an instance of the MPU6050Impl class.")
        print("[Info] The device address of the MPU6050 is " + str(hex(address)) )
        self.__csvFileWriter = csv.writer( csvFile )
        self.__address       = address
        self.__bus           = bus
        self.__bus.write_byte_data( self.__address , 0x6B , 0 )

    def __read_sensor( self ):
        try:
            mpu6050_data = self.__bus.read_i2c_block_data( self.__address , 0x3B , 14 )
            return mpu6050_data
        except:
            return None

    def doMPU6050Impl(self):
        print("[Info] Start the doMPU6050Impl function.")
        while SensorWrapper.running.is_set():
            try:
                SensorWrapper.mpu6050_cond.acquire()
                while not SensorWrapper.mpu6050_ready:
                    SensorWrapper.mpu6050_cond.wait()
                SensorWrapper.mpu6050_cond.release()

                mpu6050_data        = self.__read_sensor()
                end_unix_epoch_time = time.time()
                total_time          = end_unix_epoch_time - SensorWrapper.start_unix_epoch_time
                if mpu6050_data is not None:
                    data = [
                        [
                            total_time , SensorWrapper.start_unix_epoch_time , end_unix_epoch_time ,
                            mpu6050_data[ 0] , mpu6050_data[ 1] , mpu6050_data[ 2] ,
                            mpu6050_data[ 3] , mpu6050_data[ 4] , mpu6050_data[ 5] ,
                            mpu6050_data[ 6] , mpu6050_data[ 7] , mpu6050_data[ 8] ,
                            mpu6050_data[ 9] , mpu6050_data[10] , mpu6050_data[11] ,
                            mpu6050_data[12] , mpu6050_data[13]
                        ]
                    ]
                    self.__csvFileWriter.writerows( data )
                SensorWrapper.mpu6050_ready = False
            except (KeyboardInterrupt , ValueError) as e:
                SensorWrapper.running.clear()
            except Exception as e:
                print(e)

########################################################################
class ICM20948Impl:

    def __init__( self , address , i2cbus , csvFile ):
        print("[Info] Create an instance of the ICM20948Impl class.")
        print("[Info] The device address of the ICM-20948 is " + str(hex(address)) )
        self.__csvFileWriter = csv.writer( csvFile )
        localDriver          = qwiic_i2c.getI2CDriver( iBus=i2cbus )
        self.__imu           = qwiic_icm20948.QwiicIcm20948( address=address, i2c_driver=localDriver )

    def doIcm20948Impl(self):
        print("[Info] Start the doIcm20948Impl function.")
        self.__imu.begin()
        while SensorWrapper.running.is_set():
            try:
                SensorWrapper.icm20948_cond.acquire()
                while not SensorWrapper.icm20948_ready:
                    SensorWrapper.icm20948_cond.wait()
                SensorWrapper.icm20948_cond.release()

                if self.__imu.dataReady():
                    self.__imu.getAgmt()
                    end_unix_epoch_time = time.time()
                    total_time          = end_unix_epoch_time - SensorWrapper.start_unix_epoch_time
                    data = [
                        [
                            total_time , SensorWrapper.start_unix_epoch_time , end_unix_epoch_time ,
                            self.__imu.axRaw  , self.__imu.ayRaw , self.__imu.azRaw ,
                            self.__imu.gxRaw  , self.__imu.gyRaw , self.__imu.gzRaw ,
                            self.__imu.mxRaw  , self.__imu.myRaw , self.__imu.mxRaw ,
                            self.__imu.tmpRaw
                        ]
                    ]
                    self.__csvFileWriter.writerows( data )
                    SensorWrapper.icm20948_ready = False
            except (KeyboardInterrupt , ValueError) as e:
                SensorWrapper.running.clear()
            except Exception as e:
                print(e)

########################################################################
class GPSModuleImpl:

    def __init__( self , port  , csvFile , interval ):
        print("[Info] Create an instance of the GPSModuleImpl class.")
        print("[Info] The port for the IVK172 G-Mouse USB GPS is " + str(port) + ".")
        self.__csvFile       = csvFile
        self.__csvFileWriter = csv.writer( csvFile )
        self.__ser           = serial.Serial( port , 9600 , timeout=1 )
        self.__interval      = interval
        
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
                    gga , rmc , vtg , gsa , gsv = (
                        frame["GGA"] , frame["RMC"] , frame["VTG"] , frame["GSA"] , frame["GSV"]
                    )
                    latitude            = gga.latitude
                    longitude           = gga.longitude
                    altitude            = gga.altitude
                    altitude_units      = gga.altitude_units
                    num_sats            = gga.num_sats
                    datestamp           = rmc.datestamp
                    timestamp           = rmc.timestamp
                    spd_over_grnd       = rmc.spd_over_grnd
                    true_course         = rmc.true_course
                    true_track          = vtg.true_track
                    spd_over_grnd_kmph  = vtg.spd_over_grnd_kmph
                    pdop                = gsa.pdop
                    hdop                = gsa.hdop
                    vdo                 = gsa.vdop
                    num_sv_in_view      = gsv.num_sv_in_view
                    frame               = dict.fromkeys(frame, None)
                    end_unix_epoch_time = time.time()
                    total_time          = end_unix_epoch_time - SensorWrapper.start_unix_epoch_time
                    data = [
                        [
                            total_time , SensorWrapper.start_unix_epoch_time , end_unix_epoch_time ,
                            latitude       , longitude          , altitude       ,
                            altitude_units , num_sats           , datestamp      ,
                            timestamp      , spd_over_grnd      , true_course    ,
                            true_track     , spd_over_grnd_kmph , pdop           ,
                            hdop           , vdo                , num_sv_in_view
                        ]
                    ]
                    self.__csvFileWriter.writerows( data )
                time.sleep( self.__interval )
        except KeyboardInterrupt as e:
            pass # ignore
        finally:
            self.__ser.close()

    def doGpsModuleImpl(self):
        print("[Info] Start the doGpsModuleImpl function.")
        try:
            self.__read_sensor()
        except Exception as e:
            pass # ignore

########################################################################
class CameraModuleImpl:

    def __init__( self , csvFileName , csvFile , movieFileName , framerate , bitrate , width , height ):
        print("[Info] Create an instance of the CameraModuleImpl class.")
        self.__frame_ready   = threading.Event()
        self.__frame_count   = 0
        framerate_microsec   = int(1.0/framerate*1_000_000) # ex) 30fps = 1/30s = 33333μs
        self.__picamera2     = Picamera2()
        self.__encoder       = H264Encoder(bitrate=bitrate)
        config               = self.__picamera2.create_video_configuration(
            main     = { "format"             : "YUV420" , "size": ( width , height )       } ,
            controls = { "FrameDurationLimits": ( framerate_microsec , framerate_microsec ) }
        )
        self.__picamera2.configure( config )
        self.__picamera2.post_callback = self.__process_frame
        self.__movieFile               = movieFileName
        self.__csvFileWriter           = csv.writer( csvFile )
        self.__end_unix_epoch_time     = None

    def __process_frame( self, request ):
        SensorWrapper.camera_module_cond   .acquire()
        SensorWrapper.bme280_cond          .acquire()
        SensorWrapper.mpu6050_cond         .acquire()
        SensorWrapper.icm20948_cond        .acquire()
        SensorWrapper.powermonitor_cond    .acquire()
        SensorWrapper.camera_module_cond   .notify()
        if ((self.__frame_count % 30) == 0) :
            SensorWrapper.bme280_cond      .notify()
        if ((self.__frame_count % 150) == 0) :
            SensorWrapper.powermonitor_cond.notify()
        SensorWrapper.mpu6050_cond         .notify()
        SensorWrapper.icm20948_cond        .notify()
        SensorWrapper.camera_module_ready = True
        SensorWrapper.bme280_ready        = True
        SensorWrapper.mpu6050_ready       = True
        SensorWrapper.icm20948_ready      = True
        SensorWrapper.powermonitor_ready  = True
        SensorWrapper.camera_module_cond   .release()
        SensorWrapper.bme280_cond          .release()
        SensorWrapper.mpu6050_cond         .release()
        SensorWrapper.icm20948_cond        .release()
        SensorWrapper.powermonitor_cond    .release()
        self.__end_unix_epoch_time = time.time()
        self.__frame_count += 1
        self.__frame_ready.set()

    def __output_camera_module_csv( self ):
        while SensorWrapper.running.is_set():
            try:
                SensorWrapper.camera_module_cond.acquire()
                while not SensorWrapper.camera_module_ready:
                    SensorWrapper.camera_module_cond.wait()
                SensorWrapper.camera_module_cond.release()

                total_time = self.__end_unix_epoch_time - SensorWrapper.start_unix_epoch_time
                data = [
                    [
                        total_time , SensorWrapper.start_unix_epoch_time , self.__end_unix_epoch_time ,
                        self.__frame_count
                    ]
                ]
                self.__csvFileWriter.writerows( data )
                SensorWrapper.camera_module_ready = False
            except (KeyboardInterrupt , ValueError) as e:
                 SensorWrapper.running.clear()
            except Exception as e:
                print(e)
            
    def doCameraModuleImpl( self ):
        print("[Info] Start the doCameraModuleImpl function.")
        SensorWrapper.start_unix_epoch_time = time.time()
        cameraThread = threading.Thread( target=self.__output_camera_module_csv )
        cameraThread.start()
        self.__picamera2.start()
        self.__picamera2.start_encoder( self.__encoder , output=self.__movieFile )
        while SensorWrapper.running.is_set():
            try:
                if self.__frame_ready.wait(timeout=1.0):
                    self.__frame_ready.clear()
                cameraThread.join()
            except (KeyboardInterrupt , ValueError) as e:
                SensorWrapper.running.clear()
            except Exception as e:
                print(e)
            finally:
                self.__picamera2.stop_encoder()
                self.__picamera2.stop()
                
########################################################################
class SensorAnalyzerImpl:

    def __init__(
            self             ,
            movieFile        ,
            mp4_en           ,
            altitude_en      ,
            bme280_graph_en  ,
            mpu6050_graph_en ,
            icm20948_graph   ,
            frame_sync_en    ,
            gps_csv          ,
            bme280_csv       ,
            mpu6050_csv      ,
            icm20948_csv     ,
            movie_csv        ,
            tolerance        ,
            tolerance_gps    ,
            excel_en         ,
            map_animation_en
    ):
        print("[Info] Create an instance of the SensorAnalyzerImpl class.")
        self.__movieFile        = movieFile
        self.__mp4_en           = mp4_en
        self.__altitude_en      = altitude_en
        self.__bme280_graph_en  = bme280_graph_en
        self.__mpu6050_graph_en = mpu6050_graph_en
        self.__icm20948_graph   = icm20948_graph
        self.__frame_sync_en    = frame_sync_en
        self.__gps_csv          = gps_csv
        self.__bme280_csv       = bme280_csv
        self.__mpu6050_csv      = mpu6050_csv
        self.__icm20948_csv     = icm20948_csv
        self.__movie_csv        = movie_csv
        self.__tolerance        = tolerance
        self.__tolerance_gps    = tolerance_gps
        self.__excel_en         = excel_en
        self.__map_animation_en = map_animation_en

    def __convert_h264_to_mp4( self , movieFileName ):
        print("[Info] Start the __convert_h264_to_mp4 function.")
        start_unix_epoch_time = time.time()
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
        end_unix_epoch_time = time.time()
        total_time = end_unix_epoch_time - start_unix_epoch_time
        print("[Info] The __convert_h264_to_mp4 function takes " + str(total_time) + " seconds to run.")

    def __generate_map_html( self ):
        print("[Info] Start the __generate_map_html function.")
        dataFrame     = pandas.read_csv( self.__gps_csv )        
        dataFrame     = dataFrame.reset_index()
        dataFrame["iso_8601_time"] = pandas.to_datetime(dataFrame["unix_epoch_time"], unit='s', utc=True).dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        if self.__map_animation_en:
            features = []
            for _, row in dataFrame.iterrows():
                features.append(
                    { "type": "Feature", "geometry": { "type": "Point", "coordinates": [row["longitude"], row["latitude"]], },
                      "properties": {
                          "time"      : row["iso_8601_time"]           ,
                          "duration"  : 1000                           ,
                          "popup"     : f"{row['latitude']} , {row['longitude']}" ,
                          "icon"      : "circle"                       ,
                          "iconstyle" : {
                              "fillColor"   :"blue" ,
                              "fillOpacity" : 0.8   ,
                              "stroke"      :"true" ,
                              "radius"      : 6
                          },
                      }
                     })
            
            geojson    = { "type": "FeatureCollection", "features": features, }
            folium_map = folium.Map( location=[dataFrame["latitude"].iloc[0], dataFrame["longitude"].iloc[0]], zoom_start=10 )
            TimestampedGeoJson(
                geojson                 ,
                period         ="PT2S"  ,
                duration       ="PT0S" ,
                add_last_point =False   ,
                auto_play      =True    ,
                loop           =True    ,
                max_speed      =1       ,
            ).add_to(folium_map)
        else:
            folium_figure = folium.Figure(width=1500, height=700)
            folium_map    = folium.Map( location=[dataFrame["latitude"].iloc[0], dataFrame["longitude"].iloc[0]], zoom_start=4.5 ).add_to( folium_figure )
            folium.PolyLine(
                dataFrame[["latitude", "longitude"]].values.tolist(),
                color="blue",
                weight=3,
                opacity=0.8
            ).add_to(folium_map)
            # for i in range( dataFrame.count()["latitude"] ):
            #     folium.Marker( location=[ dataFrame.loc[ i , "latitude" ] , dataFrame.loc[ i , "longitude" ] ] ).add_to( folium_map )
        folium_map.save( self.__gps_csv + ".html" )

    def __generate_map_kml( self ):
        print("[Info] Start the __generate_map_kml function.")
        dataFrame                        = pandas.read_csv( os.path.join(os.getcwd() , self.__gps_csv ) , header=0 )
        dataFrame                        = dataFrame.reset_index()
        tuple_B                          =  [tuple(x) for x in dataFrame[['longitude','latitude','altitude']].values]
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
        dataFrame = dataFrame.reset_index()
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

    def __generate_mpu6050_graph( self ):
        print("[Info] Start the __generate_mpu6050_graph function.")

    def __analyse_frame_sync( self , bme280DataFrame ):
        print("[Info] Start the __analyse_frame_sync function.")
        if self.__movie_csv is not None:
            dataFrame = pandas.read_csv( self.__movie_csv )
            dataFrame = dataFrame.reset_index()
            dataFrame.columns             = [ 'index' , 'milli_sec_elapsed_time' ]
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
                        bme280DataFrame = bme280DataFrame.reset_index()
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
                    mpu6050DataFrame = mpu6050DataFrame.reset_index()
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
    
                if self.__icm20948_csv is not None:
                    matchTolerance  = []
                    icm20948DataFrame = pandas.read_csv( self.__icm20948_csv )
                    icm20948DataFrame = icm20948DataFrame.reset_index()
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
                    gpsDataFrame = pandas.read_csv( self.__gps_csv , index_col=None )
                    gpsDataFrame = gpsDataFrame.reset_index()
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
                                    'altitude_units'     : 'gps_altitude_units'     ,
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
        shutil.rmtree( './tmp' , ignore_errors=True )
        os.makedirs( './tmp' , exist_ok=True )
        self.__separation_h264_to_jpeg( self.__movieFile )
        cap       = cv2.VideoCapture( self.__movieFile )
        framerate = cap.get( cv2.CAP_PROP_FPS )
        self.__add_sensor_frame( dataFrame , framerate )
        self.__merge_jpeg_to_h264( self.__movieFile + ".sensor.h264" , str(framerate) )
        self.__convert_h264_to_mp4( self.__movieFile + ".sensor.h264" )
        shutil.rmtree( './tmp' , ignore_errors=True )

    def __separation_h264_to_jpeg( self , movieFileName ):
        print("[Info] Start the __separation_h264_to_jpeg function.")
        start_unix_epoch_time = time.time()
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
        end_unix_epoch_time = time.time()
        total_time = end_unix_epoch_time - start_unix_epoch_time
        print("[Info] The __separation_h264_to_jpeg function takes " + str(total_time) + " seconds to run.")

    def __add_sensor_frame( self , dataFrame , framerate ):
        print("[Info] Start the __add_sensor_frame function.")
        start_unix_epoch_time = time.time()
        imgFiles = sorted(glob.glob('tmp/frame_*.jpg'))
        frame_index = 0
        for imgFile in imgFiles:
            image    = cv2.imread(imgFile)
            text     =        "Date : " + str( dataFrame.iloc[frame_index]['current_time'] ) + "\n"
            text     = text + "Framerate : " + str( framerate ) + "\n"
            if self.__bme280_csv  is not None:
                if self.__altitude_en:
                    text = text + "BME280 Altitude : " + str( dataFrame.iloc[frame_index]['bme280_altitude'] ) + "\n"
                text = text + "BME280 Temperature : " + str( dataFrame.iloc[frame_index]['bme280_temperature'] ) + "\n"
                text = text + "BME280 Pressure : " + str( dataFrame.iloc[frame_index]['bme280_pressure'] ) + "\n"
                text = text + "BME280 Humidly : " + str( dataFrame.iloc[frame_index]['bme280_humidity'] ) + "\n"
            if self.__mpu6050_csv is not None:
                text = text + "MPU6050 AX : " + str( dataFrame.iloc[frame_index]['mpu6050_ax'] ) + "\n"
                text = text + "MPU6050 AY : " + str( dataFrame.iloc[frame_index]['mpu6050_ay'] ) + "\n"
                text = text + "MPU6050 AZ : " + str( dataFrame.iloc[frame_index]['mpu6050_az'] ) + "\n"
                text = text + "MPU6050 GX : " + str( dataFrame.iloc[frame_index]['mpu6050_gx'] ) + "\n"
                text = text + "MPU6050 GY : " + str( dataFrame.iloc[frame_index]['mpu6050_gy'] ) + "\n"
                text = text + "MPU6050 GZ : " + str( dataFrame.iloc[frame_index]['mpu6050_gz'] ) + "\n"
            if self.__icm20948_csv is not None:
                text = text + "ICM20948 AX : " + str( dataFrame.iloc[frame_index]['icm20948_ax'] ) + "\n"
                text = text + "ICM20948 AY : " + str( dataFrame.iloc[frame_index]['icm20948_ay'] ) + "\n"
                text = text + "ICM20948 AZ : " + str( dataFrame.iloc[frame_index]['icm20948_az'] ) + "\n"
                text = text + "ICM20948 GX : " + str( dataFrame.iloc[frame_index]['icm20948_gx'] ) + "\n"
                text = text + "ICM20948 GY : " + str( dataFrame.iloc[frame_index]['icm20948_gy'] ) + "\n"
                text = text + "ICM20948 GZ : " + str( dataFrame.iloc[frame_index]['icm20948_gz'] ) + "\n"
                text = text + "ICM20948 MX : " + str( dataFrame.iloc[frame_index]['icm20948_mx'] ) + "\n"
                text = text + "ICM20948 MY : " + str( dataFrame.iloc[frame_index]['icm20948_my'] ) + "\n"
                text = text + "ICM20948 MZ : " + str( dataFrame.iloc[frame_index]['icm20948_mz'] ) + "\n"
            if self.__gps_csv is not None:
                text = text + "GPS latitude : " + str( dataFrame.iloc[frame_index]['gps_latitude'] ) + "\n"
                text = text + "GPS longitude : " + str( dataFrame.iloc[frame_index]['gps_longitude'] ) + "\n"
                text = text + "GPS altitude : " + str( dataFrame.iloc[frame_index]['gps_altitude'] ) + "\n"
                text = text + "GPS altitude_unit : " + str( dataFrame.iloc[frame_index]['gps_altitude_units'] ) + "\n"
                text = text + "GPS num_sats : " + str( dataFrame.iloc[frame_index]['gps_num_sats'] ) + "\n"
                text = text + "GPS datestam : " + str( dataFrame.iloc[frame_index]['gps_datestam'] ) + "\n"
                text = text + "GPS timestamp: " + str( dataFrame.iloc[frame_index]['gps_timestamp'] ) + "\n"
                text = text + "GPS spd over grnd : " + str( dataFrame.iloc[frame_index]['gps_spd_over_grnd'] ) + "\n"
                text = text + "GPS true course : " + str( dataFrame.iloc[frame_index]['gps_true_course'] ) + "\n"
                text = text + "GPS true track : " + str( dataFrame.iloc[frame_index]['gps_true_track'] ) + "\n"
                text = text + "GPS spd over grnd kmph : " + str( dataFrame.iloc[frame_index]['gps_spd_over_grnd_kmph'] ) + "\n"
                text = text + "GPS pdop : " + str( dataFrame.iloc[frame_index]['gps_pdop'] ) + "\n"
                text = text + "GPS hdop : " + str( dataFrame.iloc[frame_index]['gps_hdop'] ) + "\n"
                text = text + "GPS vdop : " + str( dataFrame.iloc[frame_index]['gps_vdop'] ) + "\n"
                text = text + "GPS num sv in veiw : " + str( dataFrame.iloc[frame_index]['gps_num_sv_in_view'] ) + "\n"
                
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
        end_unix_epoch_time = time.time()
        total_time = end_unix_epoch_time - start_unix_epoch_time
        print("[Info] The __add_sensor_frame function takes " + str(total_time) + " seconds to run.")
            
    def __merge_jpeg_to_h264( self , movieFileName , framerate ):
        print("[Info] Start the __merge_jpeg_to_h264 function.")
        start_unix_epoch_time = time.time()
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
        end_unix_epoch_time = time.time()
        total_time = end_unix_epoch_time - start_unix_epoch_time
        print("[Info] The __merge_jpeg_to_h264 function takes " + str(total_time) + " seconds to run.")
            
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
