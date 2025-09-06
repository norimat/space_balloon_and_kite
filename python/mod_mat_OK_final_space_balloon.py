#!/usr/bin/env python3
import sys
import os
import time
import csv
import threading
import datetime
import signal
import argparse

# センサー用ライブラリ
try:
    import smbus2
    import bme280
    import serial
    import pynmea2
except ImportError:
    print("[Warn] Some sensor libraries are missing.")

# カメラ用ライブラリ
try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder
except ImportError:
    print("[Warn] Picamera2 is not installed.")

###############################################################################
# MPU9520 実装
###############################################################################
class MPU9520Impl:
    def __init__(self, bus, address=0x68):
        print("[Info] Activate MPU9520.")
        self.__address = address
        self.__bus = bus
        # MPU6050互換部分の初期化
        self.__bus.write_byte_data(self.__address, 0x6B, 0x00)
        self.__bus.write_byte_data(self.__address, 0x1A, 0x03)
        self.__bus.write_byte_data(self.__address, 0x1B, 0x00)
        self.__bus.write_byte_data(self.__address, 0x1C, 0x00)
        # AK8963（磁気センサ）初期化
        self.__mag_addr = 0x0C
        try:
            self.__bus.write_byte_data(self.__address, 0x37, 0x02)
            self.__bus.write_byte_data(self.__mag_addr, 0x0A, 0x16)
        except Exception as e:
            print(f"[Warn] Could not init AK8963: {e}")

    def read_sensor(self):
        # 加速度・ジャイロ
        try:
            data = self.__bus.read_i2c_block_data(self.__address, 0x3B, 14)
            ax = (data[0] << 8) | data[1]
            ay = (data[2] << 8) | data[3]
            az = (data[4] << 8) | data[5]
            gx = (data[8] << 8) | data[9]
            gy = (data[10] << 8) | data[11]
            gz = (data[12] << 8) | data[13]
        except Exception:
            ax = ay = az = gx = gy = gz = 0
        # 地磁気
        try:
            mag_data = self.__bus.read_i2c_block_data(self.__mag_addr, 0x03, 7)
            mx = mag_data[1] << 8 | mag_data[0]
            my = mag_data[3] << 8 | mag_data[2]
            mz = mag_data[5] << 8 | mag_data[4]
            for v in ['mx', 'my', 'mz']:
                val = locals()[v]
                if val >= 32768:
                    locals()[v] = val - 65536
        except Exception:
            mx = my = mz = 0
        return ax, ay, az, gx, gy, gz, mx, my, mz

###############################################################################
# BME280 実装
###############################################################################
class BME280Impl:
    def __init__(self, bus, address=0x76):
        self.__bus = bus
        self.__address = address

    def read_sensor(self):
        try:
            data = bme280.sample(self.__bus, self.__address)
            return data.temperature, data.pressure, data.humidity
        except Exception:
            return 0, 0, 0

###############################################################################
# GPS 実装
###############################################################################
class GPSModuleImpl:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600):
        try:
            self.__ser = serial.Serial(port, baudrate, timeout=1)
        except Exception:
            self.__ser = None

    def read_sensor(self):
        if not self.__ser:
            return 0, 0, 0
        try:
            line = self.__ser.readline().decode('ascii', errors='replace')
            if line.startswith("$GPGGA"):
                msg = pynmea2.parse(line)
                return msg.latitude, msg.longitude, msg.altitude
        except Exception:
            pass
        return 0, 0, 0

###############################################################################
# SensorWrapper
###############################################################################
class SensorWrapper:
    running = threading.Event()

    def __init__(self, argv):
        self.argv = argv
        self.__mpu9520_en = False
        self.__bme280_en = True
        self.__gps_en = True
        self.__mpu9520Impl = None
        self.__bme280Impl = None
        self.__gpsImpl = None
        self.__csv_output_dir = "./csv"
        self.__movie_output_dir = "./movie"
        self.__mpu9520_addr = 0x68
        self.__mpu9520_bus = 1
        self.__gps_port = "/dev/ttyUSB0"

        # 最新値保持
        self.ax = self.ay = self.az = 0
        self.gx = self.gy = self.gz = 0
        self.mx = self.my = self.mz = 0
        self.temp = self.press = self.hum = 0
        self.lat = self.lon = self.alt = 0

    def __read_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--mode', '-m', default=0, required=True)
        parser.add_argument('--mpu9520', action='store_true')
        parser.add_argument('--mpu9520_i2cbus', default=1)
        parser.add_argument('--mpu9520_addr', default="0x68")
        parser.add_argument('--gps_port', default="/dev/ttyUSB0")
        args = parser.parse_args(self.argv[1:])
        self.__mode = int(args.mode)
        self.__mpu9520_en = args.mpu9520
        self.__mpu9520_bus = int(args.mpu9520_i2cbus)
        self.__mpu9520_addr = int(args.mpu9520_addr, 16)
        self.__gps_port = args.gps_port

    def __setup_sensors(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.__csv_dir = os.path.join(self.__csv_output_dir, timestamp)
        self.__movie_dir = os.path.join(self.__movie_output_dir, timestamp)
        os.makedirs(self.__csv_dir, exist_ok=True)
        os.makedirs(self.__movie_dir, exist_ok=True)
        self.__csv_file_path = os.path.join(self.__csv_dir, "sensor.csv")
        self.__movie_file_path = os.path.join(self.__movie_dir, "movie.h264")

        # カメラ初期化
        self.__camera = Picamera2()
        config = self.__camera.create_video_configuration(main={"size": (1920, 1080)})
        self.__camera.configure(config)
        encoder = H264Encoder()
        self.__camera.start_recording(encoder, self.__movie_file_path)
        print("[Info] Camera recording started (FHD 1920x1080)")

        # センサー初期化
        if self.__mpu9520_en:
            self.__mpu9520Impl = MPU9520Impl(smbus2.SMBus(self.__mpu9520_bus), self.__mpu9520_addr)
        if self.__bme280_en:
            self.__bme280Impl = BME280Impl(smbus2.SMBus(1))
        if self.__gps_en:
            self.__gpsImpl = GPSModuleImpl(self.__gps_port)

    def doSensorWrapper(self):
        print("[Info] Start SensorWrapper.")
        self.__read_args()
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        if self.__mode != 0:
            print("[Warn] Only mode 0 (sensor+camera) supported.")
            return

        self.__setup_sensors()

        # CSV 書き込み準備
        csv_file = open(self.__csv_file_path, "w", newline="")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            "timestamp", "ax", "ay", "az", "gx", "gy", "gz",
            "mx", "my", "mz", "temp", "press", "hum", "lat", "lon", "alt"
        ])

        # センサースレッド
        threads = []

        def thread_mpu():
            while SensorWrapper.running.is_set():
                if self.__mpu9520Impl:
                    ax, ay, az, gx, gy, gz, mx, my, mz = self.__mpu9520Impl.read_sensor()
                    self.ax, self.ay, self.az = ax, ay, az
                    self.gx, self.gy, self.gz = gx, gy, gz
                    self.mx, self.my, self.mz = mx, my, mz
                time.sleep(1/30)

        def thread_bme():
            while SensorWrapper.running.is_set():
                if self.__bme280Impl:
                    temp, press, hum = self.__bme280Impl.read_sensor()
                    self.temp, self.press, self.hum = temp, press, hum
                time.sleep(1/30)

        def thread_gps():
            while SensorWrapper.running.is_set():
                if self.__gpsImpl:
                    lat, lon, alt = self.__gpsImpl.read_sensor()
                    self.lat, self.lon, self.alt = lat, lon, alt
                time.sleep(1/30)

        SensorWrapper.running.set()
        t_mpu = threading.Thread(target=thread_mpu)
        t_bme = threading.Thread(target=thread_bme)
        t_gps = threading.Thread(target=thread_gps)
        threads.extend([t_mpu, t_bme, t_gps])
        for t in threads:
            t.start()

        # メインループ CSV書き込み
        try:
            while True:
                timestamp = datetime.datetime.now().isoformat()
                csv_writer.writerow([
                    timestamp,
                    self.ax, self.ay, self.az,
                    self.gx, self.gy, self.gz,
                    self.mx, self.my, self.mz,
                    self.temp, self.press, self.hum,
                    self.lat, self.lon, self.alt
                ])
                csv_file.flush()
                time.sleep(1/30)
        except KeyboardInterrupt:
            print("[Info] Stopping SensorWrapper...")
            SensorWrapper.running.clear()
            for t in threads:
                t.join()
            csv_file.close()
            self.__camera.stop_recording()
            print("[Info] SensorWrapper stopped.")

###############################################################################
# Main
###############################################################################
if __name__ == "__main__":
    sw = SensorWrapper(sys.argv)
    sw.doSensorWrapper()
