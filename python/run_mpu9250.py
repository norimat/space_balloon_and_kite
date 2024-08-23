#!/usr/bin/python -u
# -*- coding: utf-8 -*-

import FaBo9Axis_MPU9250
import time

mpu9250 = FaBo9Axis_MPU9250.MPU9250()

while True:
  accel = mpu9250.readAccel()
  gyro = mpu9250.readGyro()
  magnet = mpu9250.readMagnet()
  print('accel:' + str(accel) + ', gyro:' + str(gyro) + ', agnet:'  + str(magnet))
  time.sleep(0.1)